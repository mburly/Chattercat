import os

import mysql.connector

import chattercat.constants as constants
import chattercat.twitch as twitch
from chattercat.utils import Config
import chattercat.utils as utils

ERROR_MESSAGES = constants.ERROR_MESSAGES
STATUS_MESSAGES = constants.STATUS_MESSAGES
DIRS = constants.DIRS
EMOTE_TYPES = constants.EMOTE_TYPES

class Database:
    def __init__(self, channelName):
        self.config = Config()
        self.channelDbName = f'cc_{channelName}'
        self.channelName = channelName
        self.connect()
        if self.db is None:
            self.createChannelDb()
            self.connect()

    def commit(self, sql):
        try:
            if(isinstance(sql, list)):
                for stmt in sql:
                    self.cursor.execute(stmt)
                self.db.commit()
            else:
                self.cursor.execute(sql)
                self.db.commit()
        except Exception as e:
            print(f'{self.channelName} {e}')

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

    def disconnect(self):
        if self.cursor is None:
            self.cursor.close()
        if self.db is None:
            self.db.close()

    def createChannelDb(self):
        db = connect()
        cursor = db.cursor()
        cursor.execute(self.stmtCreateDatabase())
        cursor.close()
        db.close()
        self.connect()
        self.commit([self.stmtCreateChattersTable(),self.stmtCreateSessionsTable(),self.stmtCreateGamesTable(),self.stmtCreateSegmentsTable(),
                     self.stmtCreateMessagesTable(),self.stmtCreateEmotesTable(),self.stmtCreateLogsTable(),self.stmtCreateTopEmotesProcedure(),
                     self.stmtCreateTopChattersProcedure(),self.stmtCreateRecentSessionsProcedure()])
        try:
            self.commit(self.stmtCreateEmoteStatusChangeTrigger())
        except:
            pass
        self.populateEmotesTable()
        self.downloadEmotes()

    # def createDb(self):
        # try:
            # self.connectHelper()
            # self.cursor.execute(stmtCreateDatabase(self.channel_name))
            # self.cursor.close()
            # self.db.close()
            # self.connect()
            # self.cursor.execute(stmtCreateChattersTable())
            # self.cursor.execute(stmtCreateSessionsTable())
            # self.cursor.execute(stmtCreateGamesTable())
            # self.cursor.execute(stmtCreateSegmentsTable())
            # self.cursor.execute(stmtCreateMessagesTable())
            # self.cursor.execute(stmtCreateEmotesTable())
            # self.cursor.execute(stmtCreateLogsTable())
            # self.cursor.execute(stmtCreateTopEmotesProcedure(self.channel_name))
            # self.cursor.execute(stmtCreateTopChattersProcedure(self.channel_name))
            # self.cursor.execute(stmtCreateRecentSessionsProcedure(self.channel_name))


            # 
            #   CHECK THIS CODE DID NOT ADD TO NEW METHOD
            # 
            # try:
            #     self.cursor.execute(stmtCreateEmoteStatusChangeTrigger())
            # except:
            #     pass
        # except:
        #     self.cursor.close()
        #     self.db.close()
        #     return None

    def startSession(self, stream):
        self.commit(self.stmtInsertNewSession())
        self.sessionId = self.cursor.lastrowid
        self.segment = 0
        self.addSegment(stream)
        return self.sessionId

    def endSession(self):
        self.commit([self.stmtUpdateSessionEndDatetime(),self.stmtUpdateSessionLength(),self.stmtUpdateSegmentEndDatetime(),self.stmtUpdateSegmentLength()])

    def log(self, resp):
        if(resp is None or resp.username is None or resp.message is None or resp.username == '' or ' ' in resp.username):
            return None
        self.logMessage(self.getChatterId(resp.username), resp.message)
        self.logMessageEmotes(resp.message)

    def logChatter(self, username):
        self.commit(self.stmtInsertNewChatter(username))
        return self.cursor.lastrowid

    def logEmote(self, emote, channel_id):
        source_name = emote.split('-')[0]
        id = emote.split('-')[1]
        source = EMOTE_TYPES.index(source_name)+1
        emote = twitch.getEmoteById(channel_id, id, source)
        if(emote is None):
            return None
        if('\\' in emote.code):
            emote.code = emote.code.replace('\\', '\\\\')
        self.commit(self.stmtInsertNewEmote(emote, source))

    def logMessage(self, chatter_id, message):
        if "\"" in message:
            message = message.replace("\"", "\'")
        if '\\' in message:
            message = message.replace('\\', '\\\\')
        self.commit([self.stmtInsertNewMessage(message, chatter_id),self.stmtUpdateChatterLastDate(chatter_id)])
        
    def logMessageEmotes(self, message):
        message_emotes = utils.parseMessageEmotes(self.channel_emotes, message)
        for emote in message_emotes:
            if '\\' in emote:
                emote = emote.replace('\\','\\\\')
            self.commit(self.stmtUpdateEmoteCount(emote))

    def populateEmotesTable(self):
        emotes = twitch.getAllChannelEmotes(self.channelName)
        source = 1
        for emote_type in EMOTE_TYPES:
            if(emotes[emote_type] is None):         # No emotes from source found
                source += 1
                continue
            for emote in emotes[emote_type]:
                if '\\' in emote.code:
                    emote.code = emote.code.replace('\\', '\\\\')
                self.commit(self.stmtInsertNewEmote(emote, source))
            source += 1

    def update(self):
        utils.printInfo(self.channelName, STATUS_MESSAGES['updates'])
        new_emote_count = 0
        self.channel = twitch.getChannelInfo(self.channelName)
        self.channel_id = twitch.getChannelId(self.channelName)
        channel_emotes = twitch.getAllChannelEmotes(self.channelName)
        current_emotes = self.getEmotes(channel_emotes=channel_emotes)
        previous_emotes = self.getEmotes(active=1)
        inactive_emotes = self.getEmotes(active=0)
        A = set(current_emotes)
        B = set(previous_emotes)
        C = set(inactive_emotes)
        new_emotes = A-B
        removed_emotes = B-A
        reactivated_emotes = A.intersection(C)
        for emote in new_emotes:
            if(emote in reactivated_emotes):
                continue
            self.logEmote(emote, self.channel_id)
            new_emote_count += 1
        self.setEmotesStatus(removed_emotes, 0)
        self.setEmotesStatus(reactivated_emotes, 1)
        if(new_emote_count > 0):
            self.downloadEmotes()
            utils.printInfo(self.channelName, utils.downloadMessage(new_emote_count))
        self.updateChannelPicture()
        utils.printInfo(self.channelName, STATUS_MESSAGES['updates_complete'])

    def downloadEmotesHelper(self):
        utils.printInfo(self.channelName, STATUS_MESSAGES['downloading'])
        self.cursor.execute(self.stmtSelectEmotesToDownload())
        for row in self.cursor.fetchall():
            url = row[0]
            emote_id = row[1]
            emote_name = utils.removeSymbolsFromName(row[2])
            source = int(row[3])
            if(source == 1 or source == 2):
                if('animated' in url):
                    extension = 'gif'
                else:
                    extension = 'png'
                path = f'{DIRS["twitch"]}/{emote_name}-{emote_id}.{extension}'
                download_path = f'{DIRS["twitch"]}/{emote_name}-{emote_id}.{extension}'
            elif(source == 3 or source == 4):
                extension = 'png'
                path = f'{DIRS["ffz"]}/{emote_name}-{emote_id}.{extension}'
                download_path = f'{DIRS["ffz"]}/{emote_name}-{emote_id}.{extension}'
            elif(source == 5 or source == 6):
                extension = url.split('.')[3]
                url = url.split(f'.{extension}')[0]
                path = f'{DIRS["bttv"]}/{emote_name}-{emote_id}.{extension}'
                download_path = f'{DIRS["bttv"]}/{emote_name}-{emote_id}.{extension}'
            self.commit(self.stmtUpdateEmotePath(path, emote_id, source))
            utils.downloadFile(url, download_path)

    def downloadEmotes(self):
        for dir in DIRS.values():
            if not os.path.exists(dir):
                os.mkdir(dir)
        self.downloadEmotesHelper()

    def getChannelActiveEmotes(self):
        emotes = []
        self.update()
        self.cursor.execute(self.stmtSelectActiveEmotes())
        for emote in self.cursor.fetchall():
            emotes.append(str(emote[0]))
        self.channel_emotes = emotes

    def getChatterId(self, username):
        id = None
        self.cursor.execute(self.stmtSelectChatterIdByUsername(username))
        for row in self.cursor:
            id = row[0]
            return id
        id = self.logChatter(username)
        return id

    # Returns in format: <source>-<emote_id>
    def getEmotes(self, active=None, channel_emotes=None):
        emotes = []
        if(channel_emotes is not None):
            for source in EMOTE_TYPES:
                if(channel_emotes[source] is None):
                    continue
                else:
                    for emote in channel_emotes[source]:
                        emotes.append(f'{source}-{emote.id}')
            return emotes
        else:
            emotes = []
            self.cursor.execute(self.stmtSelectEmoteByStatus(active))
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
        self.cursor.execute(self.stmtSelectGameById())
        if(len(self.cursor.fetchall()) == 0):
            self.commit(self.stmtInsertNewGame())
        self.segment += 1
        self.streamTitle = stream['title']
        self.commit(self.stmtInsertNewSegment())
        self.segmentId = self.cursor.lastrowid

    def updateChannelPicture(self):
        db = connect("cc_housekeeping")
        cursor = db.cursor(buffered=True)
        cursor.execute(self.stmtSelectProfilePictureUrl())
        if(cursor.rowcount == 0):
            cursor.execute(self.stmtInsertNewPicture())
            db.commit()
            utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channelName}.png")
        else:
            for url in cursor.fetchall():
                profile_image_url = url[0]
                if(self.channel['profile_image_url'] != profile_image_url):
                    cursor.execute(self.stmtInsertNewPicture())
                    db.commit()
                    os.replace(f"{DIRS['pictures']}/{self.channelName}.png", f"{DIRS['pictures_archive']}/{self.channelName}-{utils.getNumPhotos(self.channelName)+1}.png")
                    utils.downloadFile(self.channel["profile_image_url"], f"{DIRS['pictures']}/{self.channelName}.png")
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

    def stmtCreateTopEmotesProcedure(self):
        return f'CREATE PROCEDURE cc_{self.channelName}.topEmotes() BEGIN SELECT code, count, path FROM cc_{self.channelName}.EMOTES GROUP BY code ORDER BY count DESC LIMIT 10; END'

    def stmtCreateTopChattersProcedure(self):
        return f'CREATE PROCEDURE cc_{self.channelName}.topChatters() BEGIN SELECT c.username, COUNT(m.id) FROM cc_{self.channelName}.MESSAGES m INNER JOIN cc_{self.channelName}.CHATTERS c ON m.chatter_id=c.id GROUP BY c.username ORDER BY COUNT(m.id) DESC LIMIT 10; END'

    def stmtCreateRecentSessionsProcedure(self):
        return f'CREATE PROCEDURE cc_{self.channelName}.recentSessions() BEGIN SELECT id, (SELECT seg.stream_title FROM cc_{self.channelName}.sessions ses INNER JOIN cc_{self.channelName}.segments seg ON ses.id=seg.session_id ORDER BY seg.id DESC LIMIT 1), DATE_FORMAT(end_datetime, "%c/%e/%Y"), length FROM cc_{self.channelName}.sessions ORDER BY id DESC LIMIT 5; END'

    def stmtCreateLogsTable(self):
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

    def stmtUpdateEmotePath(self, path, emote_id, source):
        return f'UPDATE emotes SET path = "{path}" WHERE emote_id LIKE "{emote_id}" AND source LIKE "{source}";'

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
        
    def stmtInsertNewMessage(self, message, chatter_id):
        return f'INSERT INTO messages (message, session_id, segment_id, chatter_id, datetime) VALUES ("{message}", {self.sessionId}, {self.segmentId}, {chatter_id}, "{utils.getDateTime()}");'    

    def stmtInsertNewPicture(self):
        return f'INSERT INTO pictures (channel, url, date_added) VALUES ("{self.channelName}","{self.channel["profile_image_url"]}","{utils.getDateTime()}")'
    
    def stmtUpdateChatterLastDate(self, chatter_id):
        return f'UPDATE chatters SET last_date = "{utils.getDate()}" WHERE id = {chatter_id};'

    def stmtUpdateEmoteCount(self, emote):
        return f'UPDATE emotes SET count = count + 1 WHERE code = BINARY "{emote}" AND active = 1;'

    def stmtInsertNewEmote(self, emote, source):
        return f'INSERT INTO emotes (code, emote_id, url, date_added, source, active) VALUES ("{emote.code}","{emote.id}","{emote.url}","{utils.getDate()}","{source}",1);'

    def stmtUpdateEmoteStatus(self, active, emote_id):
        return f'UPDATE emotes SET active = {active} WHERE emote_id = "{emote_id}";'

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
    cursor = db.cursor()
    cursor.execute(stmtInsertExecution())
    db.commit()
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
    cursor = db.cursor()
    cursor.execute(stmtCreateAdminDatabase())
    cursor.execute('USE cc_housekeeping;')
    stmts = [stmtCreatePicturesTable(),stmtCreateAdminsTable(),stmtCreateAdminSessionsTable(),
             stmtCreateExecutionLogTable(),stmtCreateExecutionsTable()]
    for sql in stmts:
        cursor.execute(sql)
    cursor.close()
    db.close()

def updateExecution():
    db = connect("cc_housekeeping")
    cursor = db.cursor()
    cursor.execute(stmtUpdateExecution())
    db.commit()
    cursor.close()
    db.close()

def verifyAdminDb():
    db = connect("cc_housekeeping")
    if db is None:
        return False
    else:
        db.close()
        return True
    
def stmtCreateAdminDatabase():
    return 'CREATE DATABASE IF NOT EXISTS cc_housekeeping COLLATE utf8mb4_general_ci;'

def stmtCreatePicturesTable():
    return 'CREATE TABLE pictures (id INT AUTO_INCREMENT PRIMARY KEY, channel VARCHAR(256), url VARCHAR(512), date_added DATETIME)'

def stmtCreateAdminsTable():
    return 'CREATE TABLE admins (id INT AUTO_INCREMENT PRIMARY KEY, password VARCHAR(256), role INT, username VARCHAR(256))'

def stmtCreateAdminSessionsTable():
    return 'CREATE TABLE adminsessions (id INT AUTO_INCREMENT PRIMARY KEY, token VARCHAR(256), userId INT, datetime DATETIME, expires DATETIME)'

def stmtCreateExecutionLogTable():
    return 'CREATE TABLE executionlog (id INT AUTO_INCREMENT PRIMARY KEY, channel VARCHAR(256), message VARCHAR(256), type INT, datetime DATETIME)'

def stmtCreateExecutionsTable():
    return 'CREATE TABLE executions (id INT AUTO_INCREMENT PRIMARY KEY, userId INT, start DATETIME, end DATETIME)'

def stmtInsertExecution():
    return f'INSERT INTO executions (start, end, userId) VALUES ("{utils.getDateTime()}",NULL,NULL);'

def stmtUpdateExecution():
    return f'UPDATE executions SET end = "{utils.getDateTime()}" WHERE id = (SELECT MAX(id) FROM executions);'