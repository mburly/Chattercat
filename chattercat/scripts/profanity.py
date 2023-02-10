# export emote and message data to csv
# read emotes into list
# find all messages with emotes in them
# run profanity check on message
# record profanity result with emote(s)

import os
import pandas as pd
import sys
import time

from emoji import replace_emoji
from profanity_check import predict_prob

def getEmotesInMessage(emotes, message):
    message_emotes = []
    try:
        words = message.split(' ')
    except:
        return []
    for word in words:
        if word in emotes and word not in message_emotes:
            message_emotes.append(word)
    return message_emotes

def outputEmotes(emotes):
    out = ''
    for emote in emotes:
        out += f'{emote},'
    return out.rstrip(",")

def removeNonASCII(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def getDateTime():
    cur = time.localtime()
    mon = '0' if cur.tm_mon < 10 else ''
    day = '0' if cur.tm_mday < 10 else ''
    hour = '0' if cur.tm_hour < 10 else ''
    min = '0' if cur.tm_min < 10 else ''
    sec = '0' if cur.tm_sec < 10 else ''
    return f'{str(cur.tm_year)}-{mon}{str(cur.tm_mon)}-{day}{str(cur.tm_mday)}-{hour}{str(cur.tm_hour)}!{min}{str(cur.tm_min)}!{sec}{str(cur.tm_sec)}'

def scan(channel_name):
    try:
        df = pd.read_csv(f'csv/cc_{channel_name}_table_emotes.csv')
    except:
        print('Unable to open CSV file.')
        sys.exit()    

    emote_names = []
    for code in df['code']:
        emote_names.append(code)

    try:
        df = pd.read_csv(f'csv/cc_{channel_name}_table_messages.csv', encoding='iso-8859-1')
    except Exception as e:
        print(e)
        print('Unable to open CSV file.')
        sys.exit()

    if not os.path.exists('scores'):
        os.mkdir('scores')

    out_file = open(f'scores/{channel_name}-{getDateTime()}-message-scores.csv', 'w')
    header = '"score","emotes","message"'
    out_file.write(f'{header}\n')

    messages = 0
    bad_messages = 0

    print(f'Total messages: {len(df["message"])}')

    for message in df['message']:
        # print(f'Scanned {messages} messages', end='\r')
        emotes = getEmotesInMessage(emote_names, message)
        if(emotes != []):
            try:
                message = message.rstrip('\U000e0000')
                out_file.write(f'"{round(float(predict_prob([message])),5)}","{outputEmotes(emotes)}","{message}"\n')
                messages += 1
            except UnicodeEncodeError:
                message = " ".join(replace_emoji(message).split())
                message = removeNonASCII(message)
                try:
                    out_file.write(f'"{round(float(predict_prob([message])),5)}","{outputEmotes(emotes)}","{message}"\n')
                    messages += 1
                except Exception as e:
                    print(e)
                    bad_messages += 1

    print(f'Scanned {messages} messages')
    out_file.close()

    os.remove(f'csv/cc_{channel_name}_table_emotes.csv')
    os.remove(f'csv/cc_{channel_name}_table_messages.csv')
    os.rmdir('csv')