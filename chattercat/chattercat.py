import socket
import time

from chattercat.constants import ADDRESS, ADMIN_DB_NAME, ERROR_MESSAGES, TIMERS
from chattercat.db import Database, connectAdmin
import chattercat.twitch as twitch
from chattercat.utils import Response
import chattercat.utils as utils

class Chattercat:
    executing = True
    running = True
    def __init__(self, channel_name):
        self.channel_name = channel_name.lower()
        self.stream = twitch.getStreamInfo(self.channel_name)
        try:
            while(self.executing):
                if(self.stream is not None):
                    self.start()
                    while(self.running):
                        self.run()
                    self.end()
                else:
                    self.stream = twitch.getStreamInfo(self.channel_name)
                    if self.stream is None:
                        time.sleep(TIMERS['sleep'])
        except KeyboardInterrupt:
            return None

    def run(self):
        self.db.getChannelActiveEmotes()
        self.startSocket()
        self.live_clock = time.time()
        self.socket_clock = time.time()
        try:
            while(self.running):
                self.resp = ''
                if(utils.elapsedTime(self.live_clock) >= TIMERS['live']):
                    self.stream = twitch.getStreamInfo(self.channel_name)
                    if(self.stream is None):    # Try (check if live) one more time, since we are already running
                        self.stream = twitch.getStreamInfo(self.channel_name)
                    if(self.stream is not None):
                        try:
                            game_id = int(self.stream['game_id'])
                        except:
                            game_id = 0    # No game set
                        if(self.db.game_id != game_id):
                            self.db.addSegment(self.stream)
                        self.live_clock = time.time()
                    else:
                        if(self.sock is not None):
                            self.sock.close()
                        self.running = False
                if(utils.elapsedTime(self.socket_clock) >= TIMERS['socket']):
                    self.restartSocket()
                try:
                    self.resp = self.sock.recv(2048).decode('utf-8', errors='ignore')
                    if self.resp == '' :
                        self.restartSocket()
                except KeyboardInterrupt:
                    self.endExecution()
                except:
                    self.restartSocket()
                for resp in self.getResponses():
                    self.db.log(Response(self.channel_name, resp))
        except:
            self.endExecution()

            utils.printInfo(self.channel_name, utils.statusMessage(self.channel_name))
    
    def start(self):
        try:
            self.admin = connectAdmin(ADMIN_DB_NAME)
            utils.printInfo(self.channel_name, utils.statusMessage(self.channel_name))
            try:
                sql = f'INSERT INTO executionlog (type, channel, message, datetime) VALUES (1,"{self.channel_name}", "{utils.statusMessage(self.channel_name)}", UTC_TIMESTAMP());'
                self.admin.cursor().execute(sql)
                self.admin.commit()
            except Exception as e:
                print(e)
            self.db = Database(self.channel_name)
            if(self.db.startSession(self.stream) is None):
                return None
            self.running = True
        except:
            return None

    def end(self):
        self.db.endSession()
        self.db.cursor.close()
        self.db.db.close()
        self.live = False
        utils.printInfo(self.channel_name, utils.statusMessage(self.channel_name, online=False))
        sql = f'INSERT INTO executionlog (type, channel, message, datetime) VALUES (1,"{self.channel_name}", "{utils.statusMessage(self.channel_name, online=False)}", UTC_TIMESTAMP());'
        self.admin.cursor().execute(sql)
        self.admin.commit()

    def endExecution(self):
        if(self.sock is not None):
                self.sock.close()
        self.db.endSession()
        self.running = False
        self.executing = False

    def startSocket(self):
        try:
            self.sock = socket.socket()
            self.sock.connect(ADDRESS)
            self.sock.send(f'PASS {self.db.config.token}\n'.encode('utf-8'))
            self.sock.send(f'NICK {self.db.config.nickname}\n'.encode('utf-8'))
            self.sock.send(f'JOIN #{self.channel_name}\n'.encode('utf-8'))
        except:
            utils.printError(self.channel_name, ERROR_MESSAGES['host'])
            self.db.endSession()
            return None

    def restartSocket(self):
        if(self.sock is not None):
            self.sock.close()
        self.socket_clock = time.time()
        self.startSocket()

    def getResponses(self):
        try:
            return self.resp.split('\r\n')[:-1]
        except:
            return None