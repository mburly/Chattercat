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
                with open('pings.txt', 'a', encoding='UTF-8') as file:
                    file.write(f'{utils.getDateTime()} {self.channelName} PING.\n')
                try:
                    if(self.stream is not None):
                        with open('pings.txt', 'a', encoding='UTF-8') as file:
                            file.write(f'{utils.getDateTime()} {self.channelName} PING [started].\n')
                        try:
                            self.start()
                        except Exception as e:
                            utils.printInfo(self.channelName, f'Start() exception: {e}')
                        while(self.running):
                            try:
                                self.run()
                            except Exception as e:
                                utils.printInfo(self.channelName, f'run() Exception: {e}')
                        self.end()
                        with open('pings.txt', 'a', encoding='UTF-8') as file:
                            file.write(f'{utils.getDateTime()} {self.channelName} PING [ended].\n')
                    else:
                        self.stream = twitch.getStreamInfo(self.channelName)
                        if self.stream is None:
                            time.sleep(TIMERS['sleep'])
                except Exception as e:
                    utils.printInfo(self.channelName, f'executing() Exception: {e}')
        except KeyboardInterrupt:
            return None

    def run(self):
        if(self.db is None):
            utils.printInfo(self.channelName, f'DB is currently none [1]: {self.db}')
        self.db.getChannelActiveEmotes()
        self.startSocket()
        self.liveClock = time.time()
        self.socketClock = time.time()
        try:
            while(self.running):
                try:
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
                            if(self.db is None):
                                utils.printInfo(self.channelName, f'DB is currently none [2]: {self.db}')
                            if(self.db.gameId != game_id):
                                self.db.addSegment(self.stream)
                            self.liveClock = time.time()
                        else:
                            if(self.sock is not None):
                                self.sock.close()
                            self.running = False
                            break
                    if(utils.elapsedTime(self.socketClock) >= TIMERS['socket']):
                        if(self.db is None):
                            utils.printInfo(self.channelName, f'DB is currently none [3]: {self.db}')
                        self.db.disconnect()
                        self.db.connect()
                        self.restartSocket()
                    try:
                        self.resp = self.sock.recv(2048).decode('utf-8', errors='ignore')
                        if self.resp == '' :
                            self.restartSocket()
                    except KeyboardInterrupt:
                        self.endExecution()
                    except Exception as e:
                        utils.printInfo(self.channelName, f'Something happened trying to decode the socket response. restarting socket: {e}\n')
                        self.restartSocket()
                    for resp in self.getResponses():
                        try:
                            if(self.db is None):
                                utils.printInfo(self.channelName, f'DB is currently none [4]: {self.db}')
                            self.db.log(Response(self.channelName, resp))
                        except Exception as e:
                            utils.printInfo(self.channelName, f'Error logging a response: {e}\n')
                except Exception as e:
                    utils.printInfo(self.channelName, f'WITHIN run() Exception: {e}\n')
        except Exception as e:
            utils.printInfo(self.channelName, f'Exception [11]: {e}\n')
            self.endExecution()
            utils.printInfo(self.channelName, utils.statusMessage(self.channelName))
    
    def start(self):
        utils.printInfo(self.channelName, utils.statusMessage(self.channelName))
        self.db = Database(self.channelName)
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
        except Exception as e:
            utils.printError(self.channelName, ERROR_MESSAGES['host'])
            utils.printError(self.channelName, f'Extended eror info: {e}')
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