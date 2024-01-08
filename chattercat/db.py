import os

import mysql.connector

from chattercat.constants import ADMIN_DB_NAME, DB_PREFIX, DIRS, EMOTE_TYPES, EXECUTION_HANDLER_CODES, STATUS_MESSAGES, TRUNCATE_LIST
import chattercat.twitch as twitch
from chattercat.utils import Config, Response
import chattercat.utils as utils
from chattercat.warehouse import Chatter, Emote, Message, Segment, Session

class Database:
    def __init__(self, channel):
        self.channel = channel
        self.channelDbName = DB_PREFIX + self.channel.channelName
        self.config = Config()
        self.connect()
        self.exportData = {}
        self.getChannelActiveEmotes()

    def commit(self, sql, values=None):
        try:
            if(not self.db.is_connected()):
                self.connect()
            if(isinstance(sql, list)):
                for i in range(0, len(sql)):
                    try:
                        if(values):
                            if(i < len(values)):
                                self.cursor.execute(sql[i], values[i])
                            else:
                                self.cursor.execute(sql[i])
                        else:
                            self.cursor.execute(sql[i])
                    except mysql.connector.IntegrityError:
                        continue
                    except:
                        return None
                self.db.commit()
            else:
                try:
                    self.cursor.execute(sql, values)
                except:
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
        self.populateEmotesTable()
        self.downloadEmotes()
        self.commit([self.stmtCreateEmoteStatusChangeTrigger(), self.stmtCreateEmoteInsertTrigger()])

    def fetchAll(self, stmt, values=None):
        if(values):
            try:
                self.cursor.execute(stmt, values)
            except:
                return None
        else:
            try:
                self.cursor.execute(stmt)
            except:
                return None
        return self.cursor.fetchall()

    def refresh(self):
        for table in TRUNCATE_LIST:
            self.cursor.execute(self.stmtTruncateTable(table))
        self.cursor.execute(self.stmtResetEmoteCounts())

    def startSession(self, stream):
        self.commit(self.stmtInsertNewSession())
        self.sessionId = self.cursor.lastrowid
        self.segment = 0
        self.addSegment(stream)
        return self.sessionId

    def endSession(self):
        self.commit([self.stmtUpdateSessionEndDatetime(), self.stmtUpdateSessionLength(), self.stmtUpdateSegmentEndDatetime(), self.stmtUpdateSegmentLength()],
                    [(self.sessionId,), (self.sessionId,), (self.segmentId,), (self.segmentId,)])

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
        self.commit(self.stmtInsertNewChatter(), (username,))
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
        self.commit(self.stmtInsertNewEmote(), (emote.id, emote.code, emote.url, source))

    def logMessage(self, chatterId, message):
        if("\"" in message):
            message = message.replace("\"", "\'")
        if('\\' in message):
            message = message.replace('\\', '\\\\')
        if(len(message.split('ACTION :')) > 1):
            message = message.replace('ACTION :', '').lstrip()
            self.commit([self.stmtInsertNewMessage(),self.stmtUpdateChatterLastDate()],
                        [(message, 1, self.sessionId, self.segmentId, chatterId), (chatterId,)])
        elif(len(message.split('ACTION')) > 1):
            message = message.replace('ACTION', '').lstrip()
            self.commit([self.stmtInsertNewMessage(),self.stmtUpdateChatterLastDate()],
                        [(message, 1, self.sessionId, self.segmentId, chatterId), (chatterId,)])
        else:
            self.commit([self.stmtInsertNewMessage(),self.stmtUpdateChatterLastDate()],
                        [(message, 0, self.sessionId, self.segmentId, chatterId), (chatterId,)])
        
    def logMessageEmotes(self, message):
        messageEmotes = utils.parseMessageEmotes(self.channelEmotes, message)
        for emote in messageEmotes:
            if('\\' in emote):
                emote = emote.replace('\\','\\\\')
            self.commit(self.stmtUpdateEmoteCount(), (emote,))

    def populateEmotesTable(self):
        source = 1
        for emoteType in EMOTE_TYPES:
            if(self.channel.channelEmotes[emoteType] is None): # No emotes from source found
                source += 1
                continue
            for emote in self.channel.channelEmotes[emoteType]:
                if '\\' in emote.code:
                    emote.code = emote.code.replace('\\', '\\\\')
                self.commit(self.stmtInsertNewEmote(), (emote.id, emote.code, emote.url, source))
            source += 1

    def update(self):
        utils.printInfo(self.channel.channelName, STATUS_MESSAGES['updates'])
        newEmoteCount = 0
        self.channel.getEmotes()
        currentEmotes = self.getEmotes(channelEmotes=self.channel.channelEmotes)
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
            self.logEmote(emote, self.channel.channelId)
            newEmoteCount += 1
        self.setEmotesStatus(removedEmotes, 0)
        self.setEmotesStatus(reactivatedEmotes, 1)
        if(newEmoteCount > 0):
            self.downloadEmotes()
            utils.printInfo(self.channel.channelName, f'Added {newEmoteCount} new emotes.')
        self.updateChannelPicture()    
        utils.printInfo(self.channel.channelName, STATUS_MESSAGES['updates_complete'])

    def downloadEmotes(self):
        utils.printInfo(self.channel.channelName, STATUS_MESSAGES['downloading'])
        for dir in DIRS.values():
            if(not os.path.exists(dir)):
                os.mkdir(dir)
        emotes = self.fetchAll(self.stmtSelectEmotesToDownload())
        for row in emotes:
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
            self.commit(self.stmtUpdateEmotePath(), (path, emoteId, source))
            utils.downloadFile(url, path)

    def getChannelActiveEmotes(self):
        self.channelEmotes = []
        self.update()
        emotes = self.fetchAll(self.stmtSelectActiveEmotes())
        for emote in emotes:
            self.channelEmotes.append(str(emote[0]))

    def getChatterId(self, username):
        id = None
        try:
            self.cursor.execute(self.stmtSelectChatterIdByUsername(), (username,))
        except:
            return None
        for row in self.cursor:
            id = row[0]
            return id
        id = self.logChatter(username)
        return id

    # Returns in format: <source>-<emote_id>
    def getEmotes(self, active=None, channelEmotes=None):
        emoteList = []
        if(channelEmotes is not None):
            for source in EMOTE_TYPES:
                if(channelEmotes[source] is None):
                    continue
                else:
                    for emote in channelEmotes[source]:
                        emoteList.append(f'{source}-{emote.id}')
            return emoteList
        else:
            emoteList = []
            emotes = self.fetchAll(self.stmtSelectEmoteByStatus(), (active,))
            for emote in emotes:
                source = int(emote[1])
                emoteList.append(f'{EMOTE_TYPES[source-1]}-{emote[0]}')
            return emoteList

    def setEmotesStatus(self, emotes, active):
        for emote in emotes:
            id = emote.split('-')[1]
            self.commit(self.stmtUpdateEmoteStatus(), (active, id))
                
    def addSegment(self, stream):
        if(self.segment != 0):
            self.commit([self.stmtUpdateSegmentEndDatetime(),self.stmtUpdateSegmentLength()],
                        [(self.segmentId,), (self.segmentId,)])
        try:
            self.gameId = int(stream.gameId)
        except:
            self.gameId = 0
        self.gameName = stream.gameName
        gameInfo = self.fetchAll(self.stmtSelectGameById(), (self.gameId,))
        if(len(gameInfo) == 0):
            self.commit(self.stmtInsertNewGame(), (self.gameId, self.gameName))
        self.segment += 1
        self.streamTitle = stream.title
        self.commit(self.stmtInsertNewSegment(), (self.sessionId, self.streamTitle, self.segment, self.gameId))
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
            cursor.execute(self.stmtSelectProfilePictureUrl(), (self.channel.channelName,))
        except:
            return None
        if(cursor.rowcount == 0):
            try:
                cursor.execute(self.stmtInsertNewPicture(), (self.channel.channelName, self.channel['profile_image_url']))
                db.commit()
            except:
                return None
            utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channel.channelName}.png")
        else:
            try:
                for url in cursor.fetchall():
                    profileImageUrl = url[0]
                    if(self.channel['profile_image_url'] != profileImageUrl):
                        try:
                            cursor.execute(self.stmtInsertNewPicture(), (self.channel.channelName, self.channel['profile_image_url']))
                        except:
                            return None
                        db.commit()
                        os.replace(f"{DIRS['pictures']}/{self.channel.channelName}.png", f"{DIRS['pictures_archive']}/{self.channel.channelName}-{utils.getNumPhotos(self.channel.channelName)+1}.png")
                        utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channel.channelName}.png")
            except:
                return None
        cursor.close()
        db.close()

    def getChattersExport(self):
        data = {'chatters': []}
        self.exportData['newChatters'] = []
        self.exportData['chatterIdMappingsHelper'] = {}
        try:
            chatters = self.fetchAll(self.stmtGetChatters())
            for i in range(0, len(chatters)):
                c = Chatter(chatters[i][0], chatters[i][1], chatters[i][2], chatters[i][3])
                data['chatters'].append(c)
                self.exportData['newChatters'].append(c.Username)
                self.exportData['chatterIdMappingsHelper'][c.Username] = c.ChatterID
            return data['chatters']
        except:
            return []
        
    def getSessionsExport(self):
        data = {'sessions': []}
        try:
            sessions = self.fetchAll(self.stmtGetSessions())
            for session in sessions:
                data['sessions'].append(Session(session[0], session[1], session[2], session[3]))
            return data['sessions']
        except:
            return []
        
    def getGamesExport(self):
        data = {'games': {}}
        try:
            games = self.fetchAll(self.stmtGetGames())
            for game in games:
                data['games'][game[1]] = game[0]
            return data['games']
        except:
            return []
        
    def getSegmentsExport(self):
        data = {'segments': []}
        try:
            segments = self.fetchAll(self.stmtGetSegments())
            for segment in segments:
                data['segments'].append(Segment(segment[0], segment[1], segment[2], segment[3], 
                                                segment[4], segment[5], segment[6], segment[7]))
            return data['segments']
        except:
            return []
    
    def getMessagesExport(self):
        data = {'messages': []}
        try:
            messages = self.fetchAll(self.stmtGetMessages())
            for message in messages:
                data['messages'].append(Message(message[0], message[1], message[2], message[3], 
                                                message[4], message[5], message[6]))
            return data['messages']
        except:
            return []
        
    def getEmotesExport(self):
        data = {'emotes': []}
        try:
            self.exportData['emoteIds'] = []
            self.exportData['emoteCounts'] = {}
            self.exportData['emoteActives'] = {}
            emotes = self.fetchAll(self.stmtGetEmotes())
            for emote in emotes:
                e = Emote(emote[0], emote[1], emote[2], emote[3], emote[4], emote[5], emote[6], emote[7])
                self.exportData['emoteIds'].append(e.EmoteID)
                em = f'{e.EmoteID}-{e.Source}'
                self.exportData['emoteActives'][em] = e.Active
                if(e.Count > 0):
                    self.exportData['emoteCounts'][em] = e.Count
                data['emotes'].append(e)
            return data['emotes']
        except:
            return []

    def generateWarehouseExportStagingData(self):
        self.exportData['chatters'] = self.getChattersExport()
        self.exportData['sessions'] = self.getSessionsExport()
        self.exportData['games'] = self.getGamesExport()
        self.exportData['segments'] = self.getSegmentsExport()
        self.exportData['messages'] = self.getMessagesExport()
        self.exportData['emotes'] = self.getEmotesExport()
        return self.exportData

    def stmtCreateDatabase(self):
        return f'CREATE DATABASE IF NOT EXISTS {self.channelDbName} COLLATE utf8mb4_general_ci;'

    def stmtCreateChattersTable(self):
        return 'CREATE TABLE Chatters (ChatterID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(50), FirstSeen DATE, LastSeen DATE) COLLATE utf8mb4_general_ci;'

    def stmtCreateSessionsTable(self):
        return 'CREATE TABLE Sessions (SessionID INT AUTO_INCREMENT PRIMARY KEY, Start DATETIME, End DATETIME, Length TIME) COLLATE utf8mb4_general_ci;'

    def stmtCreateMessagesTable(self):
        return 'CREATE TABLE Messages (MessageID INT AUTO_INCREMENT PRIMARY KEY, Message VARCHAR(512) COLLATE utf8mb4_general_ci, Action TINYINT(1), ChatterID INT, SessionID INT, SegmentID INT, Timestamp DATETIME, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (SegmentID) REFERENCES Segments(SegmentID), FOREIGN KEY (ChatterID) REFERENCES Chatters(ChatterID)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmotesTable(self):
        return 'CREATE TABLE Emotes (EmoteID VARCHAR(255) COLLATE utf8mb4_general_ci, Code VARCHAR(255) COLLATE utf8mb4_general_ci, Count INT DEFAULT 0, URL VARCHAR(512) COLLATE utf8mb4_general_ci, Path VARCHAR(512) COLLATE utf8mb4_general_ci, Added DATE, Source INT, Active TINYINT(1), PRIMARY KEY(EmoteID, Source)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmoteLogsTable(self):
        return 'CREATE TABLE Logs (LogID INT AUTO_INCREMENT PRIMARY KEY, EmoteID VARCHAR(255), Source INT, Old INT, New INT, UserID VARCHAR(512), Timestamp DATETIME, FOREIGN KEY (EmoteID, Source) REFERENCES Emotes(EmoteID, Source)) COLLATE utf8mb4_general_ci;'

    def stmtCreateGamesTable(self):
        return 'CREATE TABLE Games (GameID INT PRIMARY KEY, Name VARCHAR(255)) COLLATE utf8mb4_general_ci;'

    def stmtCreateSegmentsTable(self):
        return 'CREATE TABLE Segments (SegmentID INT AUTO_INCREMENT PRIMARY KEY, Segment INT, Title VARCHAR(512), Start DATETIME, End DATETIME, Length TIME, SessionID INT, GameID INT, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (GameID) REFERENCES Games(GameID)) COLLATE utf8mb4_general_ci;'

    def stmtCreateTopEmotesView(self):
        return 'CREATE VIEW TopEmotesView AS SELECT Code, Count, Path, Source FROM Emotes GROUP BY Code ORDER BY Count DESC LIMIT 10;'

    def stmtCreateTopChattersView(self):
        return 'CREATE VIEW TopChattersView AS SELECT c.Username, COUNT(m.MessageID) AS MessageCount FROM Messages m INNER JOIN Chatters c ON m.ChatterID=c.ChatterID GROUP BY c.Username ORDER BY COUNT(m.MessageID) DESC LIMIT 5;'

    def stmtCreateRecentChattersView(self):
        return 'CREATE VIEW RecentChattersView AS SELECT DISTINCT (SELECT Username FROM Chatters c WHERE c.ChatterID = m.ChatterID) AS Username FROM Messages m GROUP BY MessageID ORDER BY MessageID DESC LIMIT 9;'
    
    def stmtCreateRecentMessagesView(self):
        return 'CREATE VIEW RecentMessagesView AS SELECT (SELECT c.Username FROM Chatters c WHERE c.ChatterID = m.ChatterID) AS Username, Message, Timestamp FROM Messages m ORDER BY m.MessageID DESC LIMIT 20;'

    def stmtCreateRecentSegmentsView(self):
        return 'CREATE VIEW RecentSegmentsView AS SELECT g.Name, s.Length, s.Title, s.SessionID FROM Games g INNER JOIN Segments s ON g.GameID=s.GameID WHERE s.SessionID IN (SELECT * FROM (SELECT SessionID FROM Sessions ORDER BY SessionID DESC) AS t) ORDER BY s.SegmentID DESC;'
    
    def stmtCreateRecentSessionsView(self):
        return 'CREATE VIEW RecentSessionsView AS SELECT SessionID, (SELECT seg.Title FROM Sessions ses INNER JOIN Segments seg ON ses.SessionID=seg.SessionID ORDER BY seg.SegmentID DESC LIMIT 1), DATE_FORMAT(End, "%c/%e/%Y"), Length FROM Sessions ORDER BY SessionID DESC LIMIT 5;'

    def stmtCreateEmoteStatusChangeTrigger(self):
        return 'CREATE TRIGGER EmoteStatusChangeTigger AFTER UPDATE ON Emotes FOR EACH ROW IF OLD.Active != NEW.Active THEN INSERT INTO Logs (EmoteID, Source, Old, New, UserID, Timestamp) VALUES (OLD.EmoteID, OLD.Source, OLD.Active, NEW.Active, NULL, UTC_TIMESTAMP()); END IF;'

    def stmtCreateEmoteInsertTrigger(self):
        return 'CREATE TRIGGER NewEmoteTrigger AFTER INSERT ON Emotes FOR EACH ROW INSERT INTO Logs (EmoteID, Source, Old, New, UserID, Timestamp) VALUES (NEW.EmoteID, NEW.Source, NULL, NEW.Active, NULL, UTC_TIMESTAMP());'

    def stmtSelectEmotesToDownload(self):
        return 'SELECT URL, EmoteID, Code, Source FROM Emotes WHERE Path IS NULL;'

    def stmtUpdateEmotePath(self):
        return 'UPDATE Emotes SET Path = %s WHERE EmoteID LIKE %s AND Source = %s;'

    def stmtSelectMostRecentSession(self):
        return 'SELECT MAX(SessionID) FROM Sessions;'

    def stmtUpdateSessionEndDatetime(self):
        return 'UPDATE Sessions SET End = NOW() WHERE SessionID = %s;'

    def stmtUpdateSessionLength(self):
        return 'UPDATE Sessions SET Length = (SELECT TIMEDIFF(End, Start)) WHERE SessionID = %s;'

    def stmtSelectActiveEmotes(self):
        return 'SELECT Code FROM Emotes WHERE Active = 1;'

    def stmtSelectEmoteByStatus(self):
        return 'SELECT EmoteID, Source FROM Emotes WHERE Active = %s;'

    def stmtSelectChatterIdByUsername(self):
        return 'SELECT ChatterID FROM Chatters WHERE Username = %s;'

    def stmtSelectProfilePictureUrl(self):
        return 'SELECT URL FROM Pictures WHERE Channel = %s ORDER BY PictureID DESC LIMIT 1;'

    def stmtInsertNewChatter(self):
        return 'INSERT INTO Chatters (Username, FirstSeen, LastSeen) VALUES (%s, CURDATE(), CURDATE());'
        
    def stmtInsertNewMessage(self):
        return 'INSERT INTO Messages (Message, Action, SessionID, SegmentID, ChatterID, Timestamp) VALUES (%s, %s, %s, %s, %s, NOW());'    

    def stmtInsertNewPicture(self):
        return 'INSERT INTO Pictures (Channel, URL, Added) VALUES (%s, %s, NOW());'
    
    def stmtUpdateChatterLastDate(self):
        return 'UPDATE Chatters SET LastSeen = CURDATE() WHERE ChatterID = %s;'

    def stmtUpdateEmoteCount(self):
        return 'UPDATE Emotes SET Count = Count + 1 WHERE Code = BINARY %s AND Active = 1;'

    def stmtInsertNewEmote(self):
        return 'INSERT INTO Emotes (EmoteID, Code, URL, Added, Source, Active) VALUES (%s, %s, %s, CURDATE(), %s, 1);'

    def stmtUpdateEmoteStatus(self):
        return 'UPDATE Emotes SET Active = %s WHERE EmoteID = %s;'

    def stmtInsertNewSession(self):
        return 'INSERT INTO Sessions (Start, End, Length) VALUES (NOW(), NULL, NULL);'

    def stmtSelectGameById(self):
        return 'SELECT GameID FROM Games WHERE GameID = %s;'

    def stmtInsertNewGame(self):
        self.gameName = 'N/A' if self.gameName == '' else self.gameName
        if('\"' in self.gameName):
            self.gameName = self.gameName.replace('"', '\\"')
        return 'INSERT INTO Games (GameID, Name) VALUES (%s, %s);'

    def stmtInsertNewSegment(self):
        if('\\' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('\\', '\\\\')
        if('"' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('"', '\\"')
        return 'INSERT INTO Segments (SessionID, Title, Segment, Start, End, Length, GameID) VALUES (%s, %s, %s, NOW(), NULL, NULL, %s);'

    def stmtUpdateSegmentEndDatetime(self):
        return 'UPDATE Segments SET End = NOW() WHERE SegmentID = %s;'

    def stmtUpdateSegmentLength(self):
        return 'UPDATE Segments SET Length = (SELECT TIMEDIFF(End, Start)) WHERE SegmentID = %s;'
    
    def stmtGetChatters(self):
        return 'SELECT ChatterID, Username, FirstSeen, LastSeen FROM Chatters;'
    
    def stmtGetSessions(self):
        return 'SELECT SessionID, Start, End, Length FROM Sessions;'
    
    def stmtGetGames(self):
        return 'SELECT GameID, Name FROM Games;'
    
    def stmtGetSegments(self):
        return 'SELECT SegmentID, Segment, Title, Start, End, Length, SessionID, GameID FROM Segments;'
    
    def stmtGetMessages(self):
        return 'SELECT MessageID, Message, Action, ChatterID, SessionID, SegmentID, Timestamp FROM Messages;'
    
    def stmtGetEmotes(self):
        return 'SELECT EmoteID, Code, Count, URL, Path, Added, Source, Active FROM Emotes;'
    
    def stmtTruncateTable(self, tableName):
        return f'DELETE FROM {tableName};'
    
    def stmtResetEmoteCounts(self):
        return f'UPDATE Emotes SET Count = 0;'

def executionHandler(action):
    db = connect(ADMIN_DB_NAME)
    if(db is None):
        return None
    cursor = db.cursor()
    if(cursor is None):
        return None
    try:
        if(action == EXECUTION_HANDLER_CODES['start']):
            cursor.execute(stmtInsertExecution())
        elif(action == EXECUTION_HANDLER_CODES['end']):
            cursor.execute(stmtUpdateExecution())
        else:
            return None
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
    return 'CREATE TABLE Pictures (PictureID INT AUTO_INCREMENT PRIMARY KEY, Channel VARCHAR(256), URL VARCHAR(512), Added DATETIME);'

def stmtCreateAdminsTable():
    return 'CREATE TABLE Admins (AdminID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(256), Password VARCHAR(256), Role INT);'

def stmtCreateAdminSessionsTable():
    return 'CREATE TABLE AdminSessions (AdminSessionID INT AUTO_INCREMENT PRIMARY KEY, Token VARCHAR(256), UserID INT, Timestamp DATETIME, Expires DATETIME);'

def stmtCreateExecutionsTable():
    return 'CREATE TABLE Executions (ExecutionID INT AUTO_INCREMENT PRIMARY KEY, UserID INT, Start DATETIME, End DATETIME);'

def stmtInsertExecution():
    return 'INSERT INTO Executions (Start, End, UserID) VALUES (NOW(),NULL,NULL);'

def stmtUpdateExecution():
    return 'UPDATE Executions SET End = NOW() WHERE ExecutionID = (SELECT MAX(ExecutionID) FROM Executions);'