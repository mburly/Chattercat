import socket
import time

from chattercat.constants import ADDRESS, ERROR_MESSAGES, TIMERS
from chattercat.db import Database
from chattercat.twitch import Channel
from chattercat.utils import Response
import chattercat.utils as utils
from chattercat.warehouse import Warehouse


class Chattercat:
    executing = True
    running = True
    def __init__(self, channelName):
        self.channel = Channel(channelName=channelName)
        try:
            while(self.executing):
                if(self.channel.stream.live):
                    self.start()
                    while(self.running):
                        self.run()
                    self.end()
                else:
                    self.channel.stream.getInfo()
                    if(not self.channel.stream.live):
                        time.sleep(TIMERS['sleep'])
        except KeyboardInterrupt:
            return None

    def run(self):
        self.startSocket()
        self.liveClock = time.time()
        self.socketClock = time.time()
        try:
            while(self.running):
                self.resp = ''
                if(utils.elapsedTime(self.liveClock) >= TIMERS['live']):
                    self.channel.stream.getInfo()
                    if(not self.channel.stream.live):    # Try (check if live) one more time, since we are already running
                        self.channel.stream.getInfo()
                    if(self.channel.stream.live):
                        try:
                            game_id = int(self.channel.stream.gameId)
                        except:
                            game_id = 0    # No game set
                        if(self.db.gameId != game_id):
                            self.db.addSegment(self.channel.stream)
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
                    self.db.log(Response(self.channel.channelName, resp))
        except:
            self.endExecution()
            utils.printInfo(self.channel.channelName, utils.statusMessage(self.channel.channelName))
    
    def start(self):
        utils.printInfo(self.channel.channelName, utils.statusMessage(self.channel.channelName))
        try:
            self.db = Database(self.channel)
            self.db.refresh()
        except:
            return None
        if(self.db.startSession(self.channel.stream) is None):
            return None
        self.running = True

    def end(self):
        self.db.endSession()
        utils.printInfo(self.channel.channelName, utils.statusMessage(self.channel.channelName, online=False))
        data = self.db.generateWarehouseExportStagingData()
        self.dwh = Warehouse(self.channel.channelName, data)
        self.dwh.export()
        self.dwh.disconnect()
        self.db.disconnect()
        self.running = False

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
            self.sock.send(f'JOIN #{self.channel.channelName}\n'.encode('utf-8'))
        except:
            utils.printError(self.channel.channelName, ERROR_MESSAGES['host'])
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