import os

import mysql.connector

from chattercat.constants import DIRS, EMOTE_TYPES, STATUS_MESSAGES
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
                    except:
                        return None
                self.db.commit()
            else:
                try:
                    self.cursor.execute(sql)
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
                self.createChannelDb()
                self.connect()

    def disconnect(self):
        if(self.cursor is not None):
            self.cursor.close()
        if(self.db is not None):
            self.db.close()
            
    def createChannelDb(self):
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
        self.commit([self.stmtCreateChattersTable(), self.stmtCreateSessionsTable(), self.stmtCreateGamesTable(), self.stmtCreateSegmentsTable(),
                     self.stmtCreateMessagesTable(), self.stmtCreateEmotesTable(), self.stmtCreateEmoteLogsTable(), self.stmtCreateRecentSessionsView(),
                     self.stmtCreateTopChattersView(), self.stmtCreateTopEmotesView(), self.stmtCreateRecentSegmentsView(),
                     self.stmtCreateRecentMessagesView(), self.stmtCreateRecentChattersView()])
        try:
            self.commit(self.stmtCreateEmoteStatusChangeTrigger())
        except:
            pass
        try:
            self.populateEmotesTable()
        except:
            return None
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
        self.commit([self.stmtInsertNewMessage(message, chatterId),self.stmtUpdateChatterLastDate(chatterId)])
        
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

    def updateChannelPicture(self):
        db = connect("cc_housekeeping")
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
        return f'CREATE TABLE chatters (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(512), first_date DATE, last_date DATE) COLLATE utf8mb4_general_ci;'

    def stmtCreateSessionsTable(self):
        return f'CREATE TABLE sessions (id INT AUTO_INCREMENT PRIMARY KEY, start_datetime DATETIME, end_datetime DATETIME, length TIME) COLLATE utf8mb4_general_ci;'

    def stmtCreateMessagesTable(self):
        return  f'CREATE TABLE messages (id INT AUTO_INCREMENT PRIMARY KEY, message VARCHAR(512) COLLATE utf8mb4_general_ci, session_id INT, segment_id INT, chatter_id INT, datetime DATETIME, FOREIGN KEY (session_id) REFERENCES sessions(id), FOREIGN KEY (segment_id) REFERENCES segments(id), FOREIGN KEY (chatter_id) REFERENCES chatters(id)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmotesTable(self):
        return f'CREATE TABLE emotes (id INT AUTO_INCREMENT PRIMARY KEY, code VARCHAR(255) COLLATE utf8mb4_general_ci, emote_id VARCHAR(255) COLLATE utf8mb4_general_ci, count INT DEFAULT 0, url VARCHAR(512) COLLATE utf8mb4_general_ci, path VARCHAR(512) COLLATE utf8mb4_general_ci, date_added DATE, source VARCHAR(255) COLLATE utf8mb4_general_ci, active BOOLEAN) COLLATE utf8mb4_general_ci;'

    def stmtCreateTopEmotesView(self):
        return f'CREATE VIEW top_emotes AS SELECT code, count, path, source FROM emotes GROUP BY code ORDER BY count DESC LIMIT 10;'

    def stmtCreateTopChattersView(self):
        return f'CREATE VIEW top_chatters AS SELECT c.username, COUNT(m.id) AS message_count FROM messages m INNER JOIN chatters c ON m.chatter_id=c.id GROUP BY c.username ORDER BY COUNT(m.id) DESC LIMIT 5;'

    def stmtCreateRecentChattersView(self):
        return f'CREATE VIEW recent_chatters AS SELECT DISTINCT (SELECT username FROM chatters WHERE id = chatter_id) AS username FROM messages GROUP BY id ORDER BY id DESC LIMIT 9;'
    
    def stmtCreateRecentMessagesView(self):
        return f'CREATE VIEW recent_messages AS SELECT (SELECT username FROM chatters WHERE id = chatter_id) AS username, message, datetime FROM messages ORDER BY id DESC LIMIT 20;'

    def stmtCreateRecentSegmentsView(self):
        return f'CREATE VIEW recent_segments AS SELECT g.name, s.length, s.stream_title, s.session_id FROM games g INNER JOIN segments s ON g.id=s.game_id WHERE s.session_id IN (SELECT * FROM (SELECT id FROM sessions ORDER BY id DESC) AS t) ORDER BY s.id DESC;'
    
    def stmtCreateRecentSessionsView(self):
        return f'CREATE VIEW recent_sessions AS SELECT id, (SELECT seg.stream_title FROM sessions ses INNER JOIN segments seg ON ses.id=seg.session_id ORDER BY seg.id DESC LIMIT 1), DATE_FORMAT(end_datetime, "%c/%e/%Y"), length FROM sessions ORDER BY id DESC LIMIT 5'

    def stmtCreateEmoteLogsTable(self):
        return f'CREATE TABLE logs (id INT AUTO_INCREMENT PRIMARY KEY, emote_id INT, old INT, new INT, user_id VARCHAR(512), datetime DATETIME, FOREIGN KEY (emote_id) REFERENCES emotes(id)) COLLATE utf8mb4_general_ci;'

    def stmtCreateGamesTable(self):
        return f'CREATE TABLE games (id INT PRIMARY KEY, name VARCHAR(255)) COLLATE utf8mb4_general_ci;'

    def stmtCreateSegmentsTable(self):
        return f'CREATE TABLE segments (id INT AUTO_INCREMENT PRIMARY KEY, segment INT, stream_title VARCHAR(512), start_datetime DATETIME, end_datetime DATETIME, length TIME, session_id INT, game_id INT, FOREIGN KEY (session_id) REFERENCES sessions(id), FOREIGN KEY (game_id) REFERENCES games(id)) COLLATE utf8mb4_general_ci;'

    def stmtCreateEmoteStatusChangeTrigger(self):
        return f'CREATE TRIGGER emote_status_change AFTER UPDATE ON emotes FOR EACH ROW IF OLD.active != NEW.active THEN INSERT INTO logs (emote_id, new, old, user_id, datetime) VALUES (OLD.id, NEW.active, OLD.active, NULL, UTC_TIMESTAMP()); END IF;'

    def stmtCreateEmoteInsertTrigger(self):
        return f'CREATE TRIGGER new_emote AFTER INSERT ON emotes FOR EACH ROW INSERT INTO logs (emote_id, new, old, user_id, datetime) VALUES (id, active, active, NULL, UTC_TIMESTAMP());'

    def stmtSelectEmotesToDownload(self):
        return f'SELECT url, emote_id, code, source FROM emotes WHERE path IS NULL;'

    def stmtUpdateEmotePath(self, path, emoteId, source):
        return f'UPDATE emotes SET path = "{path}" WHERE emote_id LIKE "{emoteId}" AND source LIKE "{source}";'

    def stmtSelectMostRecentSession(self):
        return f'SELECT MAX(id) FROM sessions'

    def stmtUpdateSessionEndDatetime(self):
        return f'UPDATE sessions SET end_datetime = "{utils.getDateTime()}" WHERE id = {self.sessionId}'

    def stmtUpdateSessionLength(self):
        return f'UPDATE sessions SET length = (SELECT TIMEDIFF(end_datetime, start_datetime)) WHERE id = {self.sessionId}'

    def stmtSelectActiveEmotes(self):
        return f'SELECT code FROM emotes WHERE ACTIVE = 1;'

    def stmtSelectEmoteByStatus(self, active):
        return f'SELECT emote_id, source FROM emotes WHERE active = {active};'

    def stmtSelectChatterIdByUsername(self, username):
        return f'SELECT id FROM chatters WHERE username = "{username}";'

    def stmtSelectProfilePictureUrl(self):
        return f'SELECT url FROM pictures WHERE channel = "{self.channelName}" ORDER BY id DESC LIMIT 1;'

    def stmtInsertNewChatter(self, username):
        return f'INSERT INTO chatters (username, first_date, last_date) VALUES ("{username}", "{utils.getDate()}", "{utils.getDate()}");'
        
    def stmtInsertNewMessage(self, message, chatterId):
        return f'INSERT INTO messages (message, session_id, segment_id, chatter_id, datetime) VALUES ("{message}", {self.sessionId}, {self.segmentId}, {chatterId}, "{utils.getDateTime()}");'    

    def stmtInsertNewPicture(self):
        return f'INSERT INTO pictures (channel, url, date_added) VALUES ("{self.channelName}","{self.channel["profile_image_url"]}","{utils.getDateTime()}")'
    
    def stmtUpdateChatterLastDate(self, chatterId):
        return f'UPDATE chatters SET last_date = "{utils.getDate()}" WHERE id = {chatterId};'

    def stmtUpdateEmoteCount(self, emote):
        return f'UPDATE emotes SET count = count + 1 WHERE code = BINARY "{emote}" AND active = 1;'

    def stmtInsertNewEmote(self, emote, source):
        return f'INSERT INTO emotes (code, emote_id, url, date_added, source, active) VALUES ("{emote.code}","{emote.id}","{emote.url}","{utils.getDate()}","{source}",1);'

    def stmtUpdateEmoteStatus(self, active, emoteId):
        return f'UPDATE emotes SET active = {active} WHERE emote_id = "{emoteId}";'

    def stmtInsertNewSession(self):
        return f'INSERT INTO sessions (start_datetime, end_datetime, length) VALUES ("{utils.getDateTime()}", NULL, NULL);'

    def stmtSelectGameById(self):
        return f'SELECT id FROM games WHERE id = {self.gameId};'

    def stmtInsertNewGame(self):
        self.gameName = 'N/A' if self.gameName == '' else self.gameName
        if('\"' in self.gameName):
            self.gameName = self.gameName.replace('"', '\\"')
        return f'INSERT INTO games (id, name) VALUES ({self.gameId}, "{self.gameName}");'

    def stmtInsertNewSegment(self):
        if('\\' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('\\', '\\\\')
        if('"' in self.streamTitle):
            self.streamTitle = self.streamTitle.replace('"', '\\"')
        return f'INSERT INTO segments (session_id, stream_title, segment, start_datetime, end_datetime, length, game_id) VALUES ({self.sessionId}, "{self.streamTitle}", {self.segment}, "{utils.getDateTime()}", NULL, NULL, {self.gameId});'

    def stmtSelectSegmentNumberBySessionId(self):
        return f'SELECT MAX(segment) FROM segments WHERE session_id = {self.sessionId};'

    def stmtUpdateSegmentEndDatetime(self):
        return f'UPDATE segments SET end_datetime = "{utils.getDateTime()}" WHERE id = {self.segmentId};'

    def stmtUpdateSegmentLength(self):
        return f'UPDATE segments SET length = (SELECT TIMEDIFF(end_datetime, start_datetime)) WHERE id = {self.segmentId}'

def addExecution():
    db = connect("cc_housekeeping")
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

def createHKDb():
    db = connect()
    if(db is None):
        return None
    cursor = db.cursor()
    if(cursor is None):
        return None
    try:
        cursor.execute(stmtCreateHKDatabase())
        cursor.execute('USE cc_housekeeping;')
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

def verifyHKDb():
    db = connect("cc_housekeeping")
    if db is None:
        return False
    else:
        db.close()
        return True
    
def stmtCreateHKDatabase():
    return 'CREATE DATABASE IF NOT EXISTS cc_housekeeping COLLATE utf8mb4_general_ci;'

def stmtCreatePicturesTable():
    return 'CREATE TABLE pictures (id INT AUTO_INCREMENT PRIMARY KEY, channel VARCHAR(256), url VARCHAR(512), date_added DATETIME)'

def stmtCreateAdminsTable():
    return 'CREATE TABLE admins (id INT AUTO_INCREMENT PRIMARY KEY, password VARCHAR(256), role INT, username VARCHAR(256))'

def stmtCreateAdminSessionsTable():
    return 'CREATE TABLE adminsessions (id INT AUTO_INCREMENT PRIMARY KEY, token VARCHAR(256), userId INT, datetime DATETIME, expires DATETIME)'

def stmtCreateExecutionsTable():
    return 'CREATE TABLE executions (id INT AUTO_INCREMENT PRIMARY KEY, userId INT, start DATETIME, end DATETIME)'

def stmtInsertExecution():
    return f'INSERT INTO executions (start, end, userId) VALUES ("{utils.getDateTime()}",NULL,NULL);'

def stmtUpdateExecution():
    return f'UPDATE executions SET end = "{utils.getDateTime()}" WHERE id = (SELECT MAX(id) FROM executions);'