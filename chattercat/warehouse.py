import mysql.connector

from chattercat.constants import COLORS, DWH_DB_PREFIX, STATUS_MESSAGES
from chattercat.utils import DWHConfig, getDateTime

from datetime import timedelta
import time

class Chatter:
        def __init__(self, ChatterID, Username, FirstSeen, LastSeen):
            self.ChatterID = ChatterID
            self.Username = Username
            self.FirstSeen = FirstSeen
            self.LastSeen = LastSeen

class Emote:
    def __init__(self, EmoteID, Code, Count, URL, Path, Added, Source, Active):
        self.EmoteID = EmoteID
        self.Code = Code
        self.Count = Count
        self.URL = URL
        self.Path = Path
        self.Added = Added
        self.Source = Source
        self.Active = Active

class Message:
    def __init__(self, MessageID, Message, Action, ChatterID, SessionID, SegmentID, Timestamp):
        self.MessageID = MessageID
        self.Message = Message
        self.Action = Action
        self.ChatterID = ChatterID
        self.SessionID = SessionID
        self.SegmentID = SegmentID
        self.Timestamp = Timestamp

class Segment:
    def __init__(self, SegmentID, Segment, Title, Start, End, Length, SessionID, GameID):
        self.SegmentID = SegmentID
        self.Segment = Segment
        self.Title = Title
        self.Start = Start
        self.End = End
        self.Length = Length
        self.SessionID = SessionID
        self.GameID = GameID

class Session:
    def __init__(self, SessionID, Start, End, Length):
        self.SessionID = SessionID
        self.Start = Start
        self.End = End
        self.Length = Length

class Warehouse:
    def __init__(self, channelName, data):
        self.channelName = channelName
        self.dbName = DWH_DB_PREFIX + channelName
        self.data = data
        self.chatterIdMappings = {}
        self.sessionIdMappings = {}
        self.segmentIdMappings = {}
        self.config = DWHConfig()
        if(self.connect() is None):
            return None
        
    def commit(self, sql, values=None):
        try:
            if(not self.db.is_connected()):
                self.connect()
            if(isinstance(sql, list)):
                for stmt in sql:
                    try:
                        self.cursor.execute(stmt)
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

    def connect(self):
        try:
            self.db = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
            )
            self.cursor = self.db.cursor()
            self.cursor.execute(self.stmtGetDatabases())
            databases = self.cursor.fetchall()
            for database in databases:
                if(database[0] == self.dbName):
                    self.cursor.execute(self.stmtUseDb())
                    return True
            self.cursor.execute(self.stmtCreateDb())
            self.cursor.execute(self.stmtUseDb())
            self.commit(self.setupDb())
            return True
        except:
            return None
        
    def disconnect(self):
        if(self.cursor is not None):
            self.cursor.close()
        if(self.db is not None):
            self.db.close()

    def verify(self):
        if(self.connect() is None):
            return False
        return True
    
    def setupDb(self):
        return [self.stmtCreateChattersTable(), self.stmtCreateSessionsTable(), self.stmtCreateGamesTable(), self.stmtCreateSegmentsTable(),
                self.stmtCreateMessagesTable(), self.stmtCreateEmotesTable(), self.stmtCreateExportLogsTable()]
    
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

    def export(self):
        self.printWarehouseMessage(STATUS_MESSAGES['dwh_export_start'])
        self.exportChatters()
        self.exportSessions()
        self.exportGames()
        self.exportSegments()
        self.exportMessages()
        self.exportEmotes()
        self.commit(self.stmtInsertExportLogData(), (self.exportChattersLength, len(self.data['chatters']), self.exportSessionsLength, len(self.data['sessions']), self.exportGamesLength, len(self.data['games']),
                                                    self.exportSegmentsLength, len(self.data['segments']), self.exportMessagesLength, len(self.data['messages']), self.exportEmotesLength, self.emotesProcessed))
        self.printWarehouseMessage(STATUS_MESSAGES['dwh_export_complete'])
    
    def exportChatters(self):
        self.startTimer()
        activeChatters = {}
        self.chattersProcessed = 0
        chatters = self.fetchAll(self.stmtGetArchivedChatters())
        for chatter in chatters:
            c = Chatter(chatter[0], chatter[1], None, chatter[2])
            if c.Username in self.data['newChatters']:
                activeChatters[c.Username] = c.ChatterID
                self.chatterIdMappings[self.data['chatterIdMappingsHelper'][c.Username]] = c.ChatterID
                self.data['newChatters'].remove(c.Username)
        for chatter in self.data['chatters']:
            if(chatter.Username in self.data['newChatters']):
                self.commit(self.stmtInsertNewChatter(), (chatter.Username, chatter.FirstSeen, chatter.LastSeen))
                self.chatterIdMappings[chatter.ChatterID] = self.cursor.lastrowid
            elif(chatter.Username in activeChatters):
                self.commit(self.stmtUpdateArchivedChatter(), (chatter.LastSeen, activeChatters[chatter.Username]))
        self.exportChattersLength = str(timedelta(seconds=(time.time() - self.timer)))

    def exportSessions(self):
        self.startTimer()
        self.cursor.execute(self.stmtGetNextSessionId())
        try:
            nextSessionId = int(self.cursor.fetchone()[0])+1
        except:
            nextSessionId = 1
        for session in self.data['sessions']:
            self.commit(self.stmtInsertNewSession(), (nextSessionId, session.Start, session.End, session.Length))
            self.sessionIdMappings[session.SessionID] = nextSessionId
            nextSessionId += 1
        self.exportSessionsLength = str(timedelta(seconds=(time.time() - self.timer)))

    def exportGames(self):
        self.startTimer()
        archivedGames = []
        games = self.fetchAll(self.stmtGetArchivedGames())
        for game in games:
            archivedGames.append(game[0])
        currentGameNames = self.data['games'].keys()
        for game in currentGameNames:
            if game not in archivedGames:
                self.commit(self.stmtInsertNewGame(), (self.data['games'][game], game))
        self.exportGamesLength = str(timedelta(seconds=(time.time() - self.timer)))

    def exportSegments(self):
        self.startTimer()
        self.cursor.execute(self.stmtGetNextSegmentId())
        try:
            nextSegmentId = int(self.cursor.fetchone()[0])+1
        except:
            nextSegmentId = 1
        for segment in self.data['segments']:
            self.commit(self.stmtInsertNewSegment(), 
                                (nextSegmentId, segment.Segment, segment.Title, segment.Start, 
                                segment.End, segment.Length, self.sessionIdMappings[segment.SessionID], segment.GameID))
            self.segmentIdMappings[segment.SegmentID] = nextSegmentId
            nextSegmentId += 1
        self.exportSegmentsLength = str(timedelta(seconds=(time.time() - self.timer)))

    def exportMessages(self):
        self.startTimer()
        for message in self.data['messages']:
            if(not self.chatterIdMappings):
                messageChatterId = message.ChatterID
            else:
                messageChatterId = self.chatterIdMappings[message.ChatterID]
            self.commit(self.stmtInsertNewMessage(), (message.Message, message.Action, messageChatterId, self.sessionIdMappings[message.SessionID], self.segmentIdMappings[message.SegmentID], message.Timestamp))
        self.exportMessagesLength = str(timedelta(seconds=(time.time() - self.timer)))

    def exportEmotes(self):
        self.startTimer()
        self.emotesProcessed = 0
        archivedEmotes = []
        archivedEmoteIds = []
        emotes = self.fetchAll(self.stmtGetArchivedEmotes())
        for emote in emotes:
            e = Emote(emote[0], emote[1], emote[2], emote[3], emote[4], emote[5], emote[6], emote[7])
            if(f'{e.EmoteID}-{e.Source}' in self.data['emoteCounts'].keys()):
                self.commit(self.stmtUpdateEmoteCount(), (self.data['emoteCounts'][f'{e.EmoteID}-{e.Source}'], e.EmoteID, e.Source))
                e.Count = e.Count + self.data['emoteCounts'][f'{e.EmoteID}-{e.Source}']
                self.emotesProcessed += 1
            if(f'{e.EmoteID}-{e.Source}' in self.data['emoteActives'].keys()):
                if(self.data['emoteActives'][f'{e.EmoteID}-{e.Source}'] != e.Active):
                    self.commit(self.stmtUpdateEmoteActive(), (self.data['emoteActives'][f'{e.EmoteID}-{e.Source}'], e.EmoteID, e.Source))
                    self.emotesProcessed += 1
            archivedEmotes.append(e)
            archivedEmoteIds.append(e.EmoteID)
        newEmotesToArchive = set(self.data['emoteIds'])-set(archivedEmoteIds)
        for emote in self.data['emotes']:
            if(not newEmotesToArchive):
                break
            if(emote.EmoteID in newEmotesToArchive):
                self.commit(self.stmtInsertNewEmote(), (emote.EmoteID, emote.Code, emote.Count, emote.URL, 
                                                        emote.Path, emote.Added, emote.Source, emote.Active))
                newEmotesToArchive.discard(emote.EmoteID)
                self.emotesProcessed += 1
        self.exportEmotesLength = str(timedelta(seconds=(time.time() - self.timer)))
    
    def startTimer(self):
        self.timer = time.time() 

    def printWarehouseMessage(self, message):
        print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["hi_yellow"]}WAREHOUSE{COLORS["clear"]}] [{COLORS["bold_purple"]}{self.channelName if(self.channelName is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_green"]}INFO{COLORS["clear"]}] {message}')

    def stmtCreateChattersTable(self):
        return 'CREATE TABLE Chatters (ChatterID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(512), FirstSeen DATE, LastSeen DATE) COLLATE utf8mb4_general_ci;'
    
    def stmtCreateSessionsTable(self):
        return 'CREATE TABLE Sessions (SessionID INT AUTO_INCREMENT PRIMARY KEY, Start DATETIME, End DATETIME, Length TIME) COLLATE utf8mb4_general_ci;'
    
    def stmtCreateGamesTable(self):
        return 'CREATE TABLE Games (GameID INT PRIMARY KEY, Name VARCHAR(255)) COLLATE utf8mb4_general_ci;'

    def stmtCreateSegmentsTable(self):
        return 'CREATE TABLE Segments (SegmentID INT AUTO_INCREMENT PRIMARY KEY, Segment INT, Title VARCHAR(512), Start DATETIME, End DATETIME, Length TIME, SessionID INT, GameID INT, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (GameID) REFERENCES Games(GameID)) COLLATE utf8mb4_general_ci;'
    
    def stmtCreateMessagesTable(self):
        return 'CREATE TABLE Messages (MessageID INT AUTO_INCREMENT PRIMARY KEY, Message VARCHAR(512) COLLATE utf8mb4_general_ci, Action BOOLEAN, ChatterID INT, SessionID INT, SegmentID INT, Timestamp DATETIME, FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID), FOREIGN KEY (SegmentID) REFERENCES Segments(SegmentID), FOREIGN KEY (ChatterID) REFERENCES Chatters(ChatterID)) COLLATE utf8mb4_general_ci;'
    
    def stmtCreateEmotesTable(self):
        return 'CREATE TABLE Emotes (EmoteID VARCHAR(255) COLLATE utf8mb4_general_ci, Code VARCHAR(255) COLLATE utf8mb4_general_ci, Count INT DEFAULT 0, URL VARCHAR(512) COLLATE utf8mb4_general_ci, Path VARCHAR(512) COLLATE utf8mb4_general_ci, Added DATE, Source INT, Active BOOLEAN, PRIMARY KEY(EmoteID, Source)) COLLATE utf8mb4_general_ci;'

    def stmtCreateExportLogsTable(self):
        return 'CREATE TABLE ExportLogs (ExportID INT AUTO_INCREMENT PRIMARY KEY, ChatterExportLength TIME, ChattersProcessed INT, SessionExportLength TIME, SessionsProcessed INT, GamesExportLength TIME, GamesProcessed INT, SegmentsExportLength TIME, SegmentsProcessed INT, MessagesExportLength TIME, MessagesProcessed INT, EmotesExportLength TIME, EmotesProcessed INT, Timestamp DATETIME) COLLATE utf8mb4_general_ci;'

    def stmtCreateDb(self):
        return f'CREATE DATABASE IF NOT EXISTS {self.dbName} COLLATE utf8mb4_general_ci;'
    
    def stmtGetDatabases(self):
        return 'SHOW DATABASES;'
    
    def stmtUseDb(self):
        return f'USE {self.dbName};'
    
    def stmtGetArchivedChatters(self):
        return 'SELECT ChatterID, Username, LastSeen FROM Chatters;'
    
    def stmtGetNextSessionId(self):
        return 'SELECT MAX(SessionID) FROM Sessions;'
    
    def stmtGetArchivedGames(self):
        return 'SELECT Name FROM Games;'
    
    def stmtGetNextSegmentId(self):
        return 'SELECT MAX(SegmentID) FROM Segments;'
    
    def stmtGetArchivedEmotes(self):
        return 'SELECT EmoteID, Code, Count, URL, Path, Added, Source, Active FROM Emotes;'
    
    def stmtInsertExportLogData(self):
        return 'INSERT INTO ExportLogs (ChatterExportLength, ChattersProcessed, SessionExportLength, SessionsProcessed, GamesExportLength, GamesProcessed, SegmentsExportLength, SegmentsProcessed, MessagesExportLength, MessagesProcessed, EmotesExportLength, EmotesProcessed, Timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());'
    
    def stmtInsertNewChatter(self):
        return 'INSERT INTO Chatters (Username, FirstSeen, LastSeen) VALUES (%s, %s, %s);'
    
    def stmtUpdateArchivedChatter(self):
        return 'UPDATE Chatters SET LastSeen = %s WHERE ChatterID = %s;'

    def stmtInsertNewSession(self):
        return 'INSERT INTO Sessions (SessionID, Start, End, Length) VALUES (%s, %s, %s, %s);'

    def stmtInsertNewGame(self):
        return 'INSERT INTO Games (GameID, Name) VALUES (%s, %s);'
    
    def stmtInsertNewSegment(self):
        return 'INSERT INTO Segments (SegmentID, Segment, Title, Start, End, Length, SessionID, GameID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'
    
    def stmtInsertNewMessage(self):
        return 'INSERT INTO Messages (Message, Action, ChatterID, SessionID, SegmentID, Timestamp) VALUES (%s, %s, %s, %s, %s, %s);'

    def stmtUpdateEmoteCount(self):
        return 'UPDATE Emotes SET Count = Count + %s WHERE EmoteID = %s AND Source = %s;'

    def stmtUpdateEmoteActive(self):
        return 'UPDATE Emotes SET Active = %s WHERE EmoteID = %s AND Source = %s;'
    
    def stmtInsertNewEmote(self):
        return 'INSERT INTO Emotes (EmoteID, Code, Count, URL, Path, Added, Source, Active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'