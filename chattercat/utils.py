import configparser
import os
import sys
import time

import requests

from chattercat.constants import BAD_FILE_CHARS, BANNER, COLORS, CONFIG_NAMES, CONFIG_SECTIONS, DB_VARIABLES, DIRS, ERROR_MESSAGES, EXECUTION_HANDLER_CODES, STATUS_MESSAGES, STREAMS, TWITCH_VARIABLES
import chattercat.db as db
import chattercat.twitch as twitch


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_NAMES['op'])
        self.host= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['host']]
        self.user= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['user']]
        self.password = self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['password']]
        self.nickname = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['nickname']]
        self.token = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['token']]
        self.clientId = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['client_id']]
        self.secretKey = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['secret_key']]

class DWHConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_NAMES['dwh'])
        self.host= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['host']]
        self.user= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['user']]
        self.password = self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['password']]

class Response:
    def __init__(self, channelName, response):
        self.response = response
        self.channelName = channelName
        self.username = self.parseUsername()
        self.message = self.parseMessage()
        if(self.username == self.message):
            self.username = self.parseIncompleteResponse()

    def parseIncompleteResponse(self):
        if('PRIVMSG' in self.response):
            if('@' in self.response.split('PRIVMSG')[0]):
                return self.response.split("PRIVMSG")[0].split("@")[1].split(".")[0]
        return None

    def parseUsername(self):
        try:
            if('!' in self.response):
                username = self.response.split('!')[0]
                if(':' in username):
                    return username.split(':')[1]
        except:
            return None
        return None

    def parseMessage(self):
            return self.response.split(f'#{self.channelName} :')[1] if len(self.response.split(f'#{self.channelName} :')) > 1 else None

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def downloadFile(url, fileName):
    if(not os.path.exists(fileName)):
        try:
            r = requests.get(url)
        except:
            return None
        with open(fileName, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
    return None

def elapsedTime(start):
    return (time.time() - start) / 60

def getDate():
    cur = time.gmtime()
    mon = '0' if cur.tm_mon < 10 else ''
    day = '0' if cur.tm_mday < 10 else ''
    return f'{str(cur.tm_year)}-{mon}{str(cur.tm_mon)}-{day}{str(cur.tm_mday)}'

def getDateTime(sys=False):
    cur = time.localtime() if sys else time.gmtime()
    mon = '0' if cur.tm_mon < 10 else ''
    day = '0' if cur.tm_mday < 10 else ''
    hour = '0' if cur.tm_hour < 10 else ''
    min = '0' if cur.tm_min < 10 else ''
    sec = '0' if cur.tm_sec < 10 else ''
    return f'{str(cur.tm_year)}-{mon}{str(cur.tm_mon)}-{day}{str(cur.tm_mday)} {hour}{str(cur.tm_hour)}:{min}{str(cur.tm_min)}:{sec}{str(cur.tm_sec)}'

def getNumPhotos(channelName):
    counter = 0
    for photo in os.listdir(DIRS['pictures_archive']):
        channel = photo.split('-')[0]
        if(channel == channelName):
            counter += 1
    return counter

def getStreamNames():
    streams = []
    for stream in open(STREAMS, 'r'):
        if stream != '\n':
            streams.append(stream.replace('\n',''))
    return streams

def removeSymbolsFromName(emoteName):
    counter = 0
    for character in BAD_FILE_CHARS:
        if character in emoteName:
            emoteName = emoteName.replace(character, str(counter))
            counter += 1
    return emoteName
            
def parseMessageEmotes(channelEmotes, message):
    if(type(message) == list):
        return []
    words = message.split(' ')
    parsedEmotes = []
    for word in words:
        if word in channelEmotes and word not in parsedEmotes:
            parsedEmotes.append(word)
    return parsedEmotes

def validate(streams):
    printInfo(None, STATUS_MESSAGES['validating'])
    for stream in streams:
        if(twitch.getChannelInfo(stream) is None):
            printError(stream, ERROR_MESSAGES['channel'])
            streams.remove(stream)
        else:
            printInfo(stream, STATUS_MESSAGES['channel_validated']) 
    printInfo(None, STATUS_MESSAGES['validating_complete'])
    return streams

def verify():
    printBanner()
    streams = getStreamNames()
    if(not streams):
        printError(None, ERROR_MESSAGES['no_streams'])
        sys.exit()
    streams = validate(streams)
    if(not streams):
        printError(None, ERROR_MESSAGES['invalid_streams'])
        sys.exit()
    if(db.verifyAdminDb() is False):
        db.createAdminDb()
    db.executionHandler(EXECUTION_HANDLER_CODES['start'])
    return streams

def printBanner():
    cls()
    print(f'\n{BANNER}')

def printError(channelName, message):
    print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["bold_purple"]}{channelName if(channelName is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_red"]}ERROR{COLORS["clear"]}] {message}')

def printException(channelName, message):
    print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["bold_purple"]}{channelName if(channelName is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_yellow"]}EXCEPTION{COLORS["clear"]}] {message}')

def printInfo(channelName, message):
    print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["bold_purple"]}{channelName if(channelName is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_green"]}INFO{COLORS["clear"]}] {message}')

def statusMessage(channelName, online=True):
    return f'{channelName} just went live!' if online else f'{channelName} is now offline.'