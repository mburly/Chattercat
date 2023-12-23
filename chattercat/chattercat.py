import socket
import time

from chattercat.constants import ADDRESS, ERROR_MESSAGES, TIMERS
from chattercat.db import Database
import chattercat.twitch as twitch
from chattercat.utils import Response
import chattercat.utils as utils


class Chattercat:
    executing = True
    running = True
    def __init__(self, channelName):
        self.channelName = channelName.lower()
        self.stream = twitch.getStreamInfo(self.channelName)
        try:
            while(self.executing):
                if(self.stream is not None):
                    self.start()
                    while(self.running):
                        self.run()
                    self.end()
                else:
                    self.stream = twitch.getStreamInfo(self.channelName)
                    if(self.stream is None):
                        time.sleep(TIMERS['sleep'])
        except KeyboardInterrupt:
            return None

    def run(self):
        self.db.getChannelActiveEmotes()
        self.startSocket()
        self.liveClock = time.time()
        self.socketClock = time.time()
        try:
            while(self.running):
                self.resp = ''
                if(utils.elapsedTime(self.liveClock) >= TIMERS['live']):
                    self.stream = twitch.getStreamInfo(self.channelName)
                    if(self.stream is None):    # Try (check if live) one more time, since we are already running
                        self.stream = twitch.getStreamInfo(self.channelName)
                    if(self.stream is not None):
                        try:
                            game_id = int(self.stream['game_id'])
                        except:
                            game_id = 0    # No game set
                        if(self.db.gameId != game_id):
                            self.db.addSegment(self.stream)
                        self.liveClock = time.time()
                    else:
                        if(self.sock is not None):
                            self.sock.close()
                        self.running = False
                        break
                if(utils.elapsedTime(self.socketClock) >= TIMERS['socket']):
                    self.db.disconnect()
                    self.db.connect()
                    self.restartSocket()
                try:
                    self.resp = self.sock.recv(2048).decode('utf-8', errors='ignore')
                    if(self.resp == ''):
                        self.restartSocket()
                except KeyboardInterrupt:
                    self.endExecution()
                except:
                    self.restartSocket()
                for resp in self.getResponses():
                    self.db.log(Response(self.channelName, resp))
        except:
            self.endExecution()
            utils.printInfo(self.channelName, utils.statusMessage(self.channelName))
    
    def start(self):
        utils.printInfo(self.channelName, utils.statusMessage(self.channelName))
        try:
            self.db = Database(self.channelName)
        except:
            return None
        if(self.db.startSession(self.stream) is None):
            return None
        self.running = True

    def end(self):
        self.db.endSession()
        self.db.disconnect()
        self.running = False
        utils.printInfo(self.channelName, utils.statusMessage(self.channelName, online=False))

    def endExecution(self):
        if(self.sock is not None):
            self.sock.close()
        self.db.endSession()
        self.db.disconnect()
        self.running = False
        self.executing = False

    def startSocket(self):
        try:
            self.sock = socket.socket()
            self.sock.connect(ADDRESS)
            self.sock.send(f'PASS {self.db.config.token}\n'.encode('utf-8'))
            self.sock.send(f'NICK {self.db.config.nickname}\n'.encode('utf-8'))
            self.sock.send(f'JOIN #{self.channelName}\n'.encode('utf-8'))
        except:
            utils.printError(self.channelName, ERROR_MESSAGES['host'])
            self.db.endSession()
            return None

    def restartSocket(self):
        if(self.sock is not None):
            self.sock.close()
        self.socketClock = time.time()
        self.startSocket()

    def getResponses(self):
        try:
            return self.resp.split('\r\n')[:-1]
        except:
            return None