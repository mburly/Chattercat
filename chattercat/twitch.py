import requests

import chattercat.constants as constants
import chattercat.utils as utils

API_URLS = constants.API_URLS
CDN_URLS = constants.CDN_URLS
EMOTE_TYPES = constants.EMOTE_TYPES

class Emote:
    def __init__(self, id, code, url):
        self.id = id
        self.code = code
        self.url = url

def getAllChannelEmotes(channel_name):
    channel_id = getChannelId(channel_name)
    channel_emotes = {}
    channel_emotes[EMOTE_TYPES[0]] = getTwitchEmotes()
    channel_emotes[EMOTE_TYPES[1]] = getTwitchEmotes(channel_name)
    channel_emotes[EMOTE_TYPES[2]] = getFFZEmotes()
    channel_emotes[EMOTE_TYPES[3]] = getFFZEmotes(channel_id)
    channel_emotes[EMOTE_TYPES[4]] = getBTTVEmotes()
    channel_emotes[EMOTE_TYPES[5]] = getBTTVEmotes(channel_id)
    return channel_emotes

def getBTTVEmoteById(channel_id, emote_id) -> Emote:
    url = f'{API_URLS["bttv"]}/users/twitch/{channel_id}'
    try:
        emotes = requests.get(url,params=None,headers=None).json()['sharedEmotes']
        for emote in emotes:
            if(emote['id'] == emote_id):
                return Emote(emote_id, emote['code'], f'{CDN_URLS["bttv"]}/{emote_id}/3x.{emote["imageType"]}')
        emotes = requests.get(url,params=None,headers=None).json()['channelEmotes']
        for emote in emotes:
            if(emote['id'] == emote_id):
                return Emote(emote_id, emote['code'], f'{CDN_URLS["bttv"]}/{emote_id}/3x.{emote["imageType"]}')
        # Still not found, check BTTV Global emotes
        url = f'{API_URLS["bttv"]}/emotes/global'
        emotes = requests.get(url,params=None,headers=None).json()
        for emote in emotes:
            if(emote['id'] == emote_id):
                return Emote(emote_id, emote['code'], f'{CDN_URLS["bttv"]}/{emote_id}/3x.{emote["imageType"]}')
    except:
        return None

def getBTTVEmotes(channel_id=None):
    emote_set = []
    if(channel_id is None):
        url = f'{API_URLS["bttv"]}/emotes/global'
        emotes = requests.get(url,params=None,headers=None).json()
        for i in range(0, len(emotes)):
            emote_set.append(Emote(emotes[i]['id'], emotes[i]['code'], f'{CDN_URLS["bttv"]}/{emotes[i]["id"]}/3x.{emotes[i]["imageType"]}'))
    else:
        url = f'{API_URLS["bttv"]}/users/twitch/{channel_id}'
        emotes = requests.get(url,params=None,headers=None).json()
        try:
            channel_emotes = emotes['channelEmotes']
        except:
            return None
        if(len(channel_emotes) != 0):
            for i in range(0, len(channel_emotes)):
                emote_set.append(Emote(channel_emotes[i]['id'], channel_emotes[i]['code'], f'{CDN_URLS["bttv"]}/{channel_emotes[i]["id"]}/3x.{channel_emotes[i]["imageType"]}'))
        try:
            shared_emotes = emotes['sharedEmotes']
        except:
            if(emote_set == []):
                return None
            return emote_set
        if(len(shared_emotes) != 0):
            for i in range(0, len(shared_emotes)):
                emote_set.append(Emote(shared_emotes[i]['id'], shared_emotes[i]['code'], f'{CDN_URLS["bttv"]}/{shared_emotes[i]["id"]}/3x.{shared_emotes[i]["imageType"]}'))
    return emote_set

def getChannelId(channel_name):
    try:
        return int(getChannelInfo(channel_name)['id'])
    except:
        return None

def getChannelInfo(channel_name):
    url = f'{API_URLS["twitch"]}/users?login={channel_name}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
        if('error' in resp.keys()):
            return None
        return resp['data'][0]
    except:
        return None

def getChatterColor(chatter_name):
    user_id = getChannelId(chatter_name)
    url = f'{API_URLS["twitch"]}/chat/color?user_id={user_id}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
        if('error' in resp.keys()):
            return None
        return resp['data'][0]['color']
    except:
        return None

def getEmoteById(channel_id, emote_id, source) -> Emote:
    if(source == 1 or source == 2):
        return getTwitchEmoteById(channel_id, emote_id, source)
    elif(source == 3 or source == 4):
        return getFFZEmoteById(emote_id)
    else:
        return getBTTVEmoteById(channel_id, emote_id)

def getFFZEmoteById(emote_id) -> Emote:
    url = f'{API_URLS["ffz"]}/emote/{emote_id}'
    try:
        emote = requests.get(url,params=None,headers=None).json()
        if(len(emote['emote']['urls']) == 1):
            return Emote(emote_id, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emote_id}/1')
        else:
            return Emote(emote_id, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emote_id}/4')
    except:
        return None

def getFFZEmotes(channel_id=None):
    emote_set = []
    if(channel_id is None):
        url = f'{API_URLS["ffz"]}/set/global'
        emotes = requests.get(url,params=None,headers=None).json()
        emotes = emotes['sets']['3']['emoticons']
    else:
        url = f'{API_URLS["ffz"]}/room/id/{channel_id}'
        emotes = requests.get(url,params=None,headers=None).json()
        try:
            emote_set_id = str(emotes['room']['set'])
        except:
            return None
        emotes = emotes['sets'][emote_set_id]['emoticons']
    if(emotes == []):
        return None
    for i in range(0, len(emotes)):
        if(len(emotes[i]['urls']) == 1):
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/1')
        else:
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/4')
        emote_set.append(emote)
    return emote_set

def getHeaders():
    config = utils.Config()
    return {"Authorization": f"Bearer {getOAuth(config.client_id, config.secret_key)}",
            "Client-Id": config.client_id}

def getOAuth(client_id, client_secret):
    try:
        response = requests.post(
            constants.OAUTH_URL + f'/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'
        )
        return response.json()['access_token']
    except:
        return None

def getStreamInfo(channel_name):
    url = f'{API_URLS["twitch"]}/streams?user_login={channel_name}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
        if('error' in resp.keys()):
            utils.printInfo(channel_name, resp['error'])
            return None
        return resp['data'][0]
    except:
        return None

def getTwitchEmoteById(channel_id, emote_id, source) -> Emote:
    url = f'{API_URLS["twitch"]}/chat/emotes/global' if(source == 1) else f'{API_URLS["twitch"]}/chat/emotes?broadcaster_id={channel_id}'
    try:
        emotes = requests.get(url,params=None,headers=getHeaders()).json()['data']
        for emote in emotes:
            if(emote_id == emote['id']):
                return Emote(emote_id, emote['name'], emote['images']['url_4x'])
    except:
        return None

def getTwitchEmotes(channel_name=None):
    emote_set = []
    if(channel_name is None):
        url = f'{API_URLS["twitch"]}/chat/emotes/global'
    else:
        url = f'{API_URLS["twitch"]}/chat/emotes?broadcaster_id={getChannelId(channel_name)}'
    try:
        emotes = requests.get(url,params=None,headers=getHeaders()).json()['data']
        if(emotes == []):
            return None
        for i in range(0, len(emotes)):
            if '3.0' in emotes[i]['scale']:
                if 'animated' in emotes[i]['format']:
                    url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/animated/light/3.0'
                else:
                    url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/static/light/3.0'
            else:
                url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/static/light/1.0'
            emote = Emote(emotes[i]['id'], emotes[i]['name'], url)
            emote_set.append(emote)
        return emote_set
    except:
        return None
