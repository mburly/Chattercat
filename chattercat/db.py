import os

import mysql.connector

from chattercat.constants import ADMIN_DB_NAME, DIRS, EMOTE_TYPES, STATUS_MESSAGES
import chattercat.twitch as twitch
from chattercat.utils import Config, Response
import chattercat.utils as utils


class Database:
    def __init__(self, channelName):
        self.channelDbName = f'cc_{channelName}'
        self.channelName = channelName
        self.config = Config()
        self.connect()

    def commit(self, sql):
        try:
            if(not self.db.is_connected()):
                self.connect()
            if(isinstance(sql, list)):
                for stmt in sql:
                    try:
                        self.cursor.execute(stmt)
                    except Exception as e:
                        utils.printError(self.channelName, e)
                        return None
                self.db.commit()
            else:
                try:
                    self.cursor.execute(sql)
                except Exception as e:
                    utils.printError(self.channelName, e)
                    return None
                self.db.commit()
        except:
            return None

    def connect(self, dbName=None):
        try:
            self.db = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.channelDbName if dbName is None else None
            )
            self.cursor = self.db.cursor()
        except:
            self.db = None
            if(dbName is None):
                self.create()
                self.connect()

    def disconnect(self):
        if(self.cursor is not None):
            self.cursor.close()
        if(self.db is not None):
            self.db.close()
            
    def create(self):
        db = connect()
        if(db is None):
            return None
        cursor = db.cursor()
        try:
            cursor.execute(self.stmtCreateDatabase())
        except:
            return None
        cursor.close()
        db.close()
        self.connect()
        self.commit(self.setupDb())
        try:
            self.commit(self.stmtCreateEmoteStatusChangeTrigger())
        except:
            pass
        self.populateEmotesTable()
        self.downloadEmotes()

    def startSession(self, stream):
        self.commit(self.stmtInsertNewSession())
        self.sessionId = self.cursor.lastrowid
        self.segment = 0
        self.addSegment(stream)
        return self.sessionId

    def endSession(self):
        self.commit([self.stmtUpdateSessionEndDatetime(),self.stmtUpdateSessionLength(),self.stmtUpdateSegmentEndDatetime(),self.stmtUpdateSegmentLength()])

    def log(self, resp: Response):
        if(resp is None):
            return None
        if(resp.username is None or resp.message is None or resp.username == '' or ' ' in resp.username):
            return None
        try:
            self.logMessage(self.getChatterId(resp.username), resp.message)
            self.logMessageEmotes(resp.message)
        except:
            return None

    def logChatter(self, username):
        self.commit(self.stmtInsertNewChatter(username))
        return self.cursor.lastrowid

    def logEmote(self, emote, channelId):
        sourceName = emote.split('-')[0]
        id = emote.split('-')[1]
        source = EMOTE_TYPES.index(sourceName)+1
        emote = twitch.getEmoteById(channelId, id, source)
        if(emote is None):
            return None
        if('\\' in emote.code):
            emote.code = emote.code.replace('\\', '\\\\')
        self.commit(self.stmtInsertNewEmote(emote, source))

    def logMessage(self, chatterId, message):
        if("\"" in message):
            message = message.replace("\"", "\'")
        if('\\' in message):
            message = message.replace('\\', '\\\\')
        if(len(message.split('ACTION :')) > 1):
            message = message.replace('ACTION :', '').lstrip()
            self.commit([self.stmtInsertNewMessage(message, 1, chatterId),self.stmtUpdateChatterLastDate(chatterId)])
        elif(len(message.split('ACTION')) > 1):
            message = message.replace('ACTION', '').lstrip()
            self.commit([self.stmtInsertNewMessage(message, 1, chatterId),self.stmtUpdateChatterLastDate(chatterId)])
        else:
            self.commit([self.stmtInsertNewMessage(message, 0, chatterId),self.stmtUpdateChatterLastDate(chatterId)])
        
    def logMessageEmotes(self, message):
        messageEmotes = utils.parseMessageEmotes(self.channelEmotes, message)
        for emote in messageEmotes:
            if('\\' in emote):
                emote = emote.replace('\\','\\\\')
            self.commit(self.stmtUpdateEmoteCount(emote))

    def populateEmotesTable(self):
        emotes = twitch.getAllChannelEmotes(self.channelName)
        source = 1
        for emoteType in EMOTE_TYPES:
            if(emotes[emoteType] is None):         # No emotes from source found
                source += 1
                continue
            for emote in emotes[emoteType]:
                if '\\' in emote.code:
                    emote.code = emote.code.replace('\\', '\\\\')
                self.commit(self.stmtInsertNewEmote(emote, source))
            source += 1

    def update(self):
        utils.printInfo(self.channelName, STATUS_MESSAGES['updates'])
        newEmoteCount = 0
        self.channel = twitch.getChannelInfo(self.channelName)
        self.channelId = twitch.getChannelId(self.channelName)
        channelEmotes = twitch.getAllChannelEmotes(self.channelName)
        currentEmotes = self.getEmotes(channelEmotes=channelEmotes)
        previousEmotes = self.getEmotes(active=1)
        inactiveEmotes = self.getEmotes(active=0)
        A = set(currentEmotes)
        B = set(previousEmotes)
        C = set(inactiveEmotes)
        newEmotes = A-B
        removedEmotes = B-A
        reactivatedEmotes = A.intersection(C)
        for emote in newEmotes:
            if(emote in reactivatedEmotes):
                continue
            self.logEmote(emote, self.channelId)
            newEmoteCount += 1
        self.setEmotesStatus(removedEmotes, 0)
        self.setEmotesStatus(reactivatedEmotes, 1)
        if(newEmoteCount > 0):
            self.downloadEmotes()
            utils.printInfo(self.channelName, f'Added {newEmoteCount} new emotes.')
        self.updateChannelPicture()    
        utils.printInfo(self.channelName, STATUS_MESSAGES['updates_complete'])

    def downloadEmotes(self):
        utils.printInfo(self.channelName, STATUS_MESSAGES['downloading'])
        for dir in DIRS.values():
            if(not os.path.exists(dir)):
                os.mkdir(dir)
        try:
            self.cursor.execute(self.stmtSelectEmotesToDownload())
        except:
            return None
        for row in self.cursor.fetchall():
            url = row[0]
            emoteId = row[1]
            emoteName = utils.removeSymbolsFromName(row[2])
            source = int(row[3])
            if(source == 1 or source == 2):
                if('animated' in url):
                    extension = 'gif'
                else:
                    extension = 'png'
                path = f'{DIRS["twitch"]}/{emoteName}-{emoteId}.{extension}'
            elif(source == 3 or source == 4):
                extension = 'png'
                path = f'{DIRS["ffz"]}/{emoteName}-{emoteId}.{extension}'
            elif(source == 5 or source == 6):
                extension = url.split('.')[3]
                url = url.split(f'.{extension}')[0]
                path = f'{DIRS["bttv"]}/{emoteName}-{emoteId}.{extension}'
            elif(source == 7 or source == 8):
                path = f'{DIRS["7tv"]}/{emoteName}-{emoteId}.webp'
            self.commit(self.stmtUpdateEmotePath(path, emoteId, source))
            utils.downloadFile(url, path)

    def getChannelActiveEmotes(self):
        self.channelEmotes = []
        self.update()
        try:
            self.cursor.execute(self.stmtSelectActiveEmotes())
        except:
            return None
        for emote in self.cursor.fetchall():
            self.channelEmotes.append(str(emote[0]))

    def getChatterId(self, username):
        id = None
        try:
            self.cursor.execute(self.stmtSelectChatterIdByUsername(username))
        except:
            return None
        for row in self.cursor:
            id = row[0]
            return id
        id = self.logChatter(username)
        return id

    # Returns in format: <source>-<emote_id>
    def getEmotes(self, active=None, channelEmotes=None):
        emotes = []
        if(channelEmotes is not None):
            for source in EMOTE_TYPES:
                if(channelEmotes[source] is None):
                    continue
                else:
                    for emote in channelEmotes[source]:
                        emotes.append(f'{source}-{emote.id}')
            return emotes
        else:
            emotes = []
            try:
                self.cursor.execute(self.stmtSelectEmoteByStatus(active))
            except:
                return None
            for row in self.cursor.fetchall():
                source = int(row[1])
                emotes.append(f'{EMOTE_TYPES[source-1]}-{row[0]}')
            return emotes

    def setEmotesStatus(self, emotes, active):
        for emote in emotes:
            id = emote.split('-')[1]
            self.commit(self.stmtUpdateEmoteStatus(active, id))
                
    def addSegment(self, stream):
        if(self.segment != 0):
            self.commit([self.stmtUpdateSegmentEndDatetime(),self.stmtUpdateSegmentLength()])
        try:
            self.gameId = int(stream['game_id'])
        except:
            self.gameId = 0
        self.gameName = stream['game_name']
        try:
            self.cursor.execute(self.stmtSelectGameById())
        except:
            return None
        if(len(self.cursor.fetchall()) == 0):
            self.commit(self.stmtInsertNewGame())
        self.segment += 1
        self.streamTitle = stream['title']
        self.commit(self.stmtInsertNewSegment())
        self.segmentId = self.cursor.lastrowid

    def setupDb(self):
        return [self.stmtCreateChattersTable(), self.stmtCreateSessionsTable(), self.stmtCreateGamesTable(), self.stmtCreateSegmentsTable(),
                self.stmtCreateMessagesTable(), self.stmtCreateEmotesTable(), self.stmtCreateEmoteLogsTable(), self.stmtCreateRecentSessionsView(),
                self.stmtCreateTopChattersView(), self.stmtCreateTopEmotesView(), self.stmtCreateRecentSegmentsView(),
                self.stmtCreateRecentMessagesView(), self.stmtCreateRecentChattersView()]

    def updateChannelPicture(self):
        db = connect(ADMIN_DB_NAME)
        if(db is None):
            return None
        cursor = db.cursor(buffered=True)
        if(cursor is None):
            return None
        try:
            cursor.execute(self.stmtSelectProfilePictureUrl())
        except:
            return None
        if(cursor.rowcount == 0):
            try:
                cursor.execute(self.stmtInsertNewPicture())
                db.commit()
            except:
                return None
            utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channelName}.png")
        else:
            try:
                for url in cursor.fetchall():
                    profileImageUrl = url[0]
                    if(self.channel['profile_image_url'] != profileImageUrl):
                        try:
                            cursor.execute(self.stmtInsertNewPicture())
                        except:
                            return None
                        db.commit()
                        os.replace(f"{DIRS['pictures']}/{self.channelName}.png", f"{DIRS['pictures_archive']}/{self.channelName}-{utils.getNumPhotos(self.channelName)+1}.png")
                        utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channelName}.png")
            except:
                return None
        cursor.close()
        db.close()
        
    def stmtCreateDatabase(self):
        return f'CREATE DATABASE IF NOT EXISTS cc_{self.channelName} COLLATE utf8mb4_general_ci;'

    def stmtCreateChattersTable(self):
        return f'CREATE TABLE Chatters (ChatterID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(512), FirstSeen DATE, LastSeen DATE) COLLATE utf8mb4_general_ci;'

    def stmtCreateSessionsTable(self):
        return f'CREATE TABLE Sessions (SessionID INT AUTO_INCREMENT PRIMARY KEY, Start DATETIME, End DATETIME, Length TIME) COLLATE utf8mb4_general_ci;'

    def stmtCreateMessagesTable(self):
        return  f'CREATE TABLE Messages (MessageID INT AUTO_INCREMENT PRIMARY KEY, Message VARCHAR(512) COLLATE utf8mb4_general_ci, Action BOOLEAN, ChatterID INT, SessionID INT, SegmentID INT, Timestamp DATETIME, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (SegmentID) REFERENCES Segments(SegmentID), FOREIGN KEY (ChatterID) REFERENCES Chatters(ChatterID)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmotesTable(self):
        return f'CREATE TABLE Emotes (EmoteID VARCHAR(255) COLLATE utf8mb4_general_ci, Code VARCHAR(255) COLLATE utf8mb4_general_ci, Count INT DEFAULT 0, URL VARCHAR(512) COLLATE utf8mb4_general_ci, Path VARCHAR(512) COLLATE utf8mb4_general_ci, Added DATE, Source INT, Active BOOLEAN, PRIMARY KEY(EmoteID, Source)) COLLATE utf8mb4_general_ci;'

    def stmtCreateTopEmotesView(self):
        return f'CREATE VIEW TopEmotesView AS SELECT Code, Count, Path, Source FROM Emotes GROUP BY Code ORDER BY Count DESC LIMIT 10;'

    def stmtCreateTopChattersView(self):
        return f'CREATE VIEW TopChattersView AS SELECT c.Username, COUNT(m.MessageID) AS MessageCount FROM Messages m INNER JOIN Chatters c ON m.ChatterID=c.ChatterID GROUP BY c.Username ORDER BY COUNT(m.MessageID) DESC LIMIT 5;'

    def stmtCreateRecentChattersView(self):
        return f'CREATE VIEW RecentChattersView AS SELECT DISTINCT (SELECT Username FROM Chatters c WHERE c.ChatterID = m.ChatterID) AS Username FROM Messages m GROUP BY MessageID ORDER BY MessageID DESC LIMIT 9;'
    
    def stmtCreateRecentMessagesView(self):
        return f'CREATE VIEW RecentMessagesView AS SELECT (SELECT c.Username FROM Chatters c WHERE c.ChatterID = m.ChatterID) AS Username, Message, Timestamp FROM Messages m ORDER BY m.MessageID DESC LIMIT 20;'

    def stmtCreateRecentSegmentsView(self):
        return f'CREATE VIEW RecentSegmentsView AS SELECT g.Name, s.Length, s.Title, s.SessionID FROM Games g INNER JOIN Segments s ON g.GameID=s.GameID WHERE s.SessionID IN (SELECT * FROM (SELECT SessionID FROM Sessions ORDER BY SessionID DESC) AS t) ORDER BY s.SegmentID DESC;'
    
    def stmtCreateRecentSessionsView(self):
        return f'CREATE VIEW RecentSessionsView AS SELECT SessionID, (SELECT seg.Title FROM Sessions ses INNER JOIN Segments seg ON ses.SessionID=seg.SessionID ORDER BY seg.SegmentID DESC LIMIT 1), DATE_FORMAT(End, "%c/%e/%Y"), Length FROM Sessions ORDER BY SessionID DESC LIMIT 5'

    def stmtCreateEmoteLogsTable(self):
        return f'CREATE TABLE Logs (LogID INT AUTO_INCREMENT PRIMARY KEY, EmoteID VARCHAR(255), Source INT, Old INT, New INT, UserID VARCHAR(512), Timestamp DATETIME, FOREIGN KEY (EmoteID, Source) REFERENCES Emotes(EmoteID, Source)) COLLATE utf8mb4_general_ci;'

    def stmtCreateGamesTable(self):
        return f'CREATE TABLE Games (GameID INT PRIMARY KEY, Name VARCHAR(255)) COLLATE utf8mb4_general_ci;'

    def stmtCreateSegmentsTable(self):
        return f'CREATE TABLE Segments (SegmentID INT AUTO_INCREMENT PRIMARY KEY, Segment INT, Title VARCHAR(512), Start DATETIME, End DATETIME, Length TIME, SessionID INT, GameID INT, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (GameID) REFERENCES Games(GameID)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmoteStatusChangeTrigger(self):
        return f'CREATE TRIGGER EmoteStatusChangeTigger AFTER UPDATE ON Emotes FOR EACH ROW IF OLD.Active != NEW.Active THEN INSERT INTO Logs (EmoteID, Source, Old, New, UserID, Timestamp) VALUES (OLD.EmoteID, OLD.Source, OLD.Active, NEW.Active, NULL, UTC_TIMESTAMP()); END IF;'

    def stmtSelectEmotesToDownload(self):
        return f'SELECT URL, EmoteID, Code, Source FROM Emotes WHERE Path IS NULL;'

    def stmtUpdateEmotePath(self, path, emoteId, source):
        return f'UPDATE Emotes SET Path = "{path}" WHERE EmoteID LIKE "{emoteId}" AND Source = {source};'

    def stmtSelectMostRecentSession(self):
        return f'SELECT MAX(SessionID) FROM Sessions'

    def stmtUpdateSessionEndDatetime(self):
        return f'UPDATE Sessions SET End = "{utils.getDateTime()}" WHERE SessionID = {self.sessionId}'

    def stmtUpdateSessionLength(self):
        return f'UPDATE Sessions SET Length = (SELECT TIMEDIFF(End, Start)) WHERE SessionID = {self.sessionId}'

    def stmtSelectActiveEmotes(self):
        return f'SELECT Code FROM Emotes WHERE Active = 1;'

    def stmtSelectEmoteByStatus(self, active):
        return f'SELECT EmoteID, Source FROM Emotes WHERE Active = {active};'

    def stmtSelectChatterIdByUsername(self, username):
        return f'SELECT ChatterID FROM Chatters WHERE Username = "{username}";'

    def stmtSelectProfilePictureUrl(self):
        return f'SELECT URL FROM Pictures WHERE Channel = "{self.channelName}" ORDER BY PictureID DESC LIMIT 1;'

    def stmtInsertNewChatter(self, username):
        return f'INSERT INTO Chatters (Username, FirstSeen, LastSeen) VALUES ("{username}", "{utils.getDate()}", "{utils.getDate()}");'
        
    def stmtInsertNewMessage(self, message, action, chatterId):
        return f'INSERT INTO Messages (Message, Action, SessionID, SegmentID, ChatterID, Timestamp) VALUES ("{message}", {action}, {self.sessionId}, {self.segmentId}, {chatterId}, "{utils.getDateTime()}");'    

    def stmtInsertNewPicture(self):
        return f'INSERT INTO Pictures (Channel, URL, Added) VALUES ("{self.channelName}","{self.channel["profile_image_url"]}","{utils.getDateTime()}")'
    
    def stmtUpdateChatterLastDate(self, chatterId):
        return f'UPDATE Chatters SET LastSeen = "{utils.getDate()}" WHERE ChatterID = {chatterId};'

    def stmtUpdateEmoteCount(self, emote):
        return f'UPDATE Emotes SET Count = Count + 1 WHERE Code = BINARY "{emote}" AND Active = 1;'

    def stmtInsertNewEmote(self, emote, source):
        return f'INSERT INTO Emotes (EmoteID, Code, URL, Added, Source, Active) VALUES ("{emote.id}","{emote.code}","{emote.url}","{utils.getDate()}", {source}, 1);'

    def stmtUpdateEmoteStatus(self, active, emoteId):
        return f'UPDATE Emotes SET Active = {active} WHERE EmoteID = "{emoteId}";'

    def stmtInsertNewSession(self):
        return f'INSERT INTO Sessions (Start, End, Length) VALUES ("{utils.getDateTime()}", NULL, NULL);'

    def stmtSelectGameById(self):
        return f'SELECT GameID FROM Games WHERE GameID = {self.gameId};'

    def stmtInsertNewGame(self):
        self.gameName = 'N/A' if self.gameName == '' else self.gameName
        if('\"' in self.gameName):
            self.gameName = self.gameName.replace('"', '\\"')
        return f'INSERT INTO Games (GameID, Name) VALUES ({self.gameId}, "{self.gameName}");'

    def stmtInsertNewSegment(self):
        if('\\' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('\\', '\\\\')
        if('"' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('"', '\\"')
        return f'INSERT INTO Segments (SessionID, Title, Segment, Start, End, Length, GameID) VALUES ({self.sessionId}, "{self.streamTitle}", {self.segment}, "{utils.getDateTime()}", NULL, NULL, {self.gameId});'

    def stmtSelectSegmentNumberBySessionId(self):
        return f'SELECT MAX(Segment) FROM Segments WHERE SessionID = {self.sessionId};'

    def stmtUpdateSegmentEndDatetime(self):
        return f'UPDATE Segments SET End = "{utils.getDateTime()}" WHERE SegmentID = {self.segmentId};'

    def stmtUpdateSegmentLength(self):
        return f'UPDATE Segments SET Length = (SELECT TIMEDIFF(End, Start)) WHERE SegmentID = {self.segmentId}'

def addExecution():
    db = connect(ADMIN_DB_NAME)
    if(db is None):
        return None
    cursor = db.cursor()
    if(cursor is None):
        return None
    try:
        cursor.execute(stmtInsertExecution())
        db.commit()
    except:
        if(cursor is not None):
            cursor.close()
        if(db is not None):
            db.close()
        return None
    cursor.close()
    db.close()

def connect(dbName=None):
        try:
            c = Config()
            db = mysql.connector.connect(
                host=c.host,
                user=c.user,
                password=c.password,
                database=dbName if dbName is not None else None
            )
            return db
        except:
            return None    

def createAdminDb():
    db = connect()
    if(db is None):
        return None
    cursor = db.cursor()
    if(cursor is None):
        return None
    try:
        cursor.execute(stmtCreateAdminDatabase())
        cursor.execute(f'USE {ADMIN_DB_NAME};')
    except:
        return None
    stmts = [stmtCreatePicturesTable(),stmtCreateAdminsTable(),stmtCreateAdminSessionsTable(),
             stmtCreateExecutionsTable()]
    try:
        for sql in stmts:
            try:
                cursor.execute(sql)
            except:
                continue
    except:
        return None
    cursor.close()
    db.close()

def verifyAdminDb():
    db = connect(ADMIN_DB_NAME)
    if db is None:
        return False
    else:
        db.close()
        return True
    
def stmtCreateAdminDatabase():
    return f'CREATE DATABASE IF NOT EXISTS {ADMIN_DB_NAME} COLLATE utf8mb4_general_ci;'

def stmtCreatePicturesTable():
    return 'CREATE TABLE Pictures (PictureID INT AUTO_INCREMENT PRIMARY KEY, Channel VARCHAR(256), URL VARCHAR(512), Added DATETIME)'

def stmtCreateAdminsTable():
    return 'CREATE TABLE Admins (AdminID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(256), Password VARCHAR(256), Role INT)'

def stmtCreateAdminSessionsTable():
    return 'CREATE TABLE AdminSessions (AdminSessionID INT AUTO_INCREMENT PRIMARY KEY, Token VARCHAR(256), UserID INT, Timestamp DATETIME, Expires DATETIME)'

def stmtCreateExecutionsTable():
    return 'CREATE TABLE Executions (ExecutionID INT AUTO_INCREMENT PRIMARY KEY, UserID INT, Start DATETIME, End DATETIME)'

def stmtInsertExecution():
    return f'INSERT INTO Executions (Start, End, UserID) VALUES ("{utils.getDateTime()}",NULL,NULL);'

def stmtUpdateExecution():
    return f'UPDATE Executions SET End = "{utils.getDateTime()}" WHERE ExecutionID = (SELECT MAX(ExecutionID) FROM Executions);'