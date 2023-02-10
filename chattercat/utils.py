import configparser
import os
import sys
import time

import mysql.connector
import requests

import chattercat.constants as constants
import chattercat.twitch as twitch

COLORS = constants.COLORS
CONFIG_SECTIONS = constants.CONFIG_SECTIONS
DB_VARIABLES = constants.DB_VARIABLES
DIRS = constants.DIRS
ERROR_MESSAGES = constants.ERROR_MESSAGES
TWITCH_VARIABLES = constants.TWITCH_VARIABLES

class InvalidConfigValue(Exception):
    pass

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(constants.CONFIG_NAME)
        self.host= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['host']]
        self.user= self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['user']]
        self.password = self.config[CONFIG_SECTIONS['db']][DB_VARIABLES['password']]
        self.nickname = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['nickname']]
        self.token = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['token']]
        self.client_id = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['client_id']]
        self.secret_key = self.config[CONFIG_SECTIONS['twitch']][TWITCH_VARIABLES['secret_key']]

class Response:
    def __init__(self, channel_name, response):
        self.response = response
        self.channel_name = channel_name
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
            return self.response.split('!')[0].split(':')[1]
        except:
            return None

    def parseMessage(self):
        try:
            return self.response.split(f'#{self.channel_name} :')[1]
        except:
            return None

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

# Used when connecting to a non cc_{channelname} db 
# i.e. when wanting to connect to cc_housekeeping
def connect(db_name):
    conf = Config()
    try:
        db = mysql.connector.connect(
            host=conf.host,
            user=conf.user,
            password=conf.password,
        database=db_name if db_name is not None else None
        )
        return db
    except Exception as e:
        raise e

def createAdminDb():
    db = connect(None)
    cursor = db.cursor()
    sql = 'CREATE DATABASE IF NOT EXISTS cc_housekeeping COLLATE utf8mb4_general_ci;'
    cursor.execute(sql)
    sql = 'USE cc_housekeeping;'
    cursor.execute(sql)
    sql = 'CREATE TABLE pictures (id INT AUTO_INCREMENT PRIMARY KEY, channel VARCHAR(256), url VARCHAR(512), date_added DATETIME)'
    cursor.execute(sql)
    sql = 'CREATE TABLE admins (id INT AUTO_INCREMENT PRIMARY KEY, password VARCHAR(256), role INT, username VARCHAR(256))'
    cursor.execute(sql)
    sql = 'INSERT INTO admins (username, password, role) VALUES ("michael","21232f297a57a5a743894a0e4a801fc3",1);'
    cursor.execute(sql)
    db.commit()
    sql = 'CREATE TABLE adminsessions (id INT AUTO_INCREMENT PRIMARY KEY, token VARCHAR(256), userId INT, datetime DATETIME, expires DATETIME)'
    cursor.execute(sql)
    sql = 'CREATE TABLE executionlog (id INT AUTO_INCREMENT PRIMARY KEY, channel VARCHAR(256), message VARCHAR(256), type INT, datetime DATETIME)'
    cursor.execute(sql)
    sql = 'CREATE TABLE executions (id INT AUTO_INCREMENT PRIMARY KEY, userId INT, start DATETIME, end DATETIME)'
    cursor.execute(sql)
    cursor.close()
    db.close()

def verifyAdminDb():
    try:
        db = connect("cc_housekeeping")
        db.close()
        return True
    except mysql.connector.ProgrammingError:
        return False

def downloadFile(url, fileName):
    if not os.path.exists(fileName):
        r = requests.get(url)
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

def getNumPhotos(channel_name):
    counter = 0;
    for photo in os.listdir(DIRS['pictures_archive']):
        channel = photo.split('-')[0]
        if(channel == channel_name):
            counter += 1
    return counter

def getStreamNames():
    streams = []
    for stream in open(constants.STREAMS, 'r'):
        streams.append(stream.replace('\n',''))
    return streams

def removeSymbolsFromName(emote_name):
    counter = 0
    for character in constants.BAD_FILE_CHARS:
        if character in emote_name:
            emote_name = emote_name.replace(character, str(counter))
            counter += 1
    return emote_name
            
def parseMessageEmotes(channel_emotes, message):
    if(type(message) == list):
        return []
    words = message.split(' ')
    parsed_emotes = []
    for word in words:
        if word in channel_emotes and word not in parsed_emotes:
            parsed_emotes.append(word)
    return parsed_emotes

def verify():
    printBanner()
    streams = getStreamNames()
    if(len(streams) == 0):
        printError(None, ERROR_MESSAGES['no_streams'])
        sys.exit()
    try:
        twitch.getChannelId(streams[0])
    except InvalidConfigValue:
        printError(None, ERROR_MESSAGES['config'])
        sys.exit()
    if(verifyAdminDb() is False):
        createAdminDb()
    return streams

def printBanner():
    cls()
    print(f'\n{constants.BANNER}')

def printError(channel_name, text):
    print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["bold_purple"]}{channel_name if(channel_name is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_red"]}ERROR{COLORS["clear"]}] {text}')

def printInfo(channel_name, text):
    print(f'[{COLORS["bold_blue"]}{getDateTime(True)}{COLORS["clear"]}] [{COLORS["bold_purple"]}{channel_name if(channel_name is not None) else "Chattercat"}{COLORS["clear"]}] [{COLORS["hi_green"]}INFO{COLORS["clear"]}] {text}')

def statusMessage(channel_name, online=True):
    return f'{channel_name} just went live!' if online else f'{channel_name} is now offline.'

def downloadMessage(new_emote_count):
    return f'Downloaded {new_emote_count} newly active emotes.'