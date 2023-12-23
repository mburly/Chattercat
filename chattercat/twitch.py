import requests

from chattercat.constants import API_URLS, CDN_URLS, EMOTE_TYPES, OAUTH_URL
from chattercat.utils import Config, printException


class Emote:
    def __init__(self, id, code, url):
        self.id = id
        self.code = code
        self.url = url

def getAllChannelEmotes(channelName):
    channelId = getChannelId(channelName)
    channelEmotes = {}
    emoteFunctions = {
        'twitch': getTwitchEmotes,
        'subscriber': getTwitchEmotes,
        'ffz': getFFZEmotes,
        'ffz_channel': getFFZEmotes,
        'bttv': getBTTVEmotes,
        'bttv_channel': getBTTVEmotes,
        '7tv': get7TVEmotes,
        '7tv_channel': get7TVEmotes
    }
    for i, emoteType in enumerate(EMOTE_TYPES):
        channelEmotes[emoteType] = emoteFunctions[emoteType](channelId) if i % 2 else emoteFunctions[emoteType]()
    return channelEmotes

def get7TVEmoteById(emoteId) -> Emote:
    url = f'{API_URLS["7tv"]}/emotes/{emoteId}'
    try:
        resp = requests.get(url,params=None,headers=None).json()
    except:
        return None
    if(resp is None):
        return None
    respKeys = resp.keys()
    if 'name' in respKeys:
        return Emote(emoteId, resp['name'], f"{CDN_URLS['7tv'].replace('#', emoteId)}")
    return None

def get7TVEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["7tv"]}/emote-sets/62cdd34e72a832540de95857'
        try:
            resp = requests.get(url,params=None,headers=None).json()
        except:
            return None
        if(resp is None):
            return None
        if('emotes' in resp.keys()):
            emotes = resp['emotes']
            for emote in emotes:
                emoteSet.append(Emote(emote['id'], emote['name'], f"{CDN_URLS['7tv'].replace('#', emote['id'])}"))
    else:
        url = f'{API_URLS["7tv"]}/users/twitch/{channelId}'
        try:
            resp = requests.get(url,params=None,headers=None).json()
        except:
            return None
        if(resp is None):
            return None
        if('emote_set' in resp.keys()):
            if(resp['emote_set'] is None):
                return None
            if('emotes' in resp['emote_set'].keys()):
                for emote in resp['emote_set']['emotes']:
                    emoteSet.append(Emote(emote['id'], emote['name'], CDN_URLS['7tv'].replace('#', emote['id'])))
    return emoteSet

def getBTTVEmoteById(channelId, emoteId) -> Emote:
    url = f'{API_URLS["bttv"]}/users/twitch/{channelId}'
    try:
        resp = requests.get(url,params=None,headers=None).json()
    except:
        return None
    if(resp is None):
        return None
    if('sharedEmotes' in resp.keys()):
        emotes = resp['sharedEmotes']
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')
    try:
        resp = requests.get(url,params=None,headers=None).json()
    except:
        return None
    if(resp is None):
        return None
    if('channelEmotes' in resp.keys()):
        emotes = resp['channelEmotes']
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')
        # Still not found, search BTTV Global emotes
        url = f'{API_URLS["bttv"]}/emotes/global'
        try:
            emotes = requests.get(url,params=None,headers=None).json()
        except:
            return None
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')

def getBTTVEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["bttv"]}/emotes/global'
        try:
            emotes = requests.get(url,params=None,headers=None).json()
        except:
            return None
        for i in range(0, len(emotes)):
            emoteSet.append(Emote(emotes[i]['id'], emotes[i]['code'], f'{CDN_URLS["bttv"]}/{emotes[i]["id"]}/3x.{emotes[i]["imageType"]}'))
    else:
        url = f'{API_URLS["bttv"]}/users/twitch/{channelId}'
        try:
            resp = requests.get(url,params=None,headers=None).json()
        except:
            return None
        if(resp is None):
            return None
        if('channelEmotes' in resp.keys()):
            channelEmotes = resp['channelEmotes']
            if(len(channelEmotes) != 0):
                for i in range(0, len(channelEmotes)):
                    emoteSet.append(Emote(channelEmotes[i]['id'], channelEmotes[i]['code'], f'{CDN_URLS["bttv"]}/{channelEmotes[i]["id"]}/3x.{channelEmotes[i]["imageType"]}'))
        if('sharedEmotes' in resp.keys()):
            sharedEmotes = resp['sharedEmotes']
            if(len(sharedEmotes) != 0):
                for i in range(0, len(sharedEmotes)):
                    emoteSet.append(Emote(sharedEmotes[i]['id'], sharedEmotes[i]['code'], f'{CDN_URLS["bttv"]}/{sharedEmotes[i]["id"]}/3x.{sharedEmotes[i]["imageType"]}'))
    return emoteSet

def getChannelId(channelName):
    channelInfo = getChannelInfo(channelName)
    if(channelInfo is None):
        return None
    if('id' in channelInfo.keys()):
        return int(channelInfo['id'])
    return None

def getChannelInfo(channelName):
    url = f'{API_URLS["twitch"]}/users?login={channelName}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
    except:
        return None
    if(resp is None):
        return None
    if('data' in resp.keys()):
        if(not resp['data']):
            return None
        return resp['data'][0]
    return None

def getEmoteById(channelId, emoteId, source) -> Emote:
    if(source == 1 or source == 2):
        return getTwitchEmoteById(channelId, emoteId, source)
    elif(source == 3 or source == 4):
        return getFFZEmoteById(emoteId)
    elif(source == 5 or source == 6):
        return getBTTVEmoteById(channelId, emoteId)
    elif(source == 7 or source == 8):
        return get7TVEmoteById(emoteId)
    return None

def getFFZEmoteById(emoteId) -> Emote:
    url = f'{API_URLS["ffz"]}/emote/{emoteId}'
    try:
        emote = requests.get(url,params=None,headers=None).json()
    except:
        return None
    if(emote is None):
        return None
    if('emote' in emote.keys()):
        if('urls' in emote['emote'].keys()):
            if(len(emote['emote']['urls']) == 1):
                return Emote(emoteId, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emoteId}/1')
            else:
                return Emote(emoteId, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emoteId}/4')

def getFFZEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["ffz"]}/set/global'
        try:
            emotes = requests.get(url,params=None,headers=None).json()
        except:
            return None
        if(emotes is None):
            return None
        if('sets' in emotes.keys()):
            if('3' in emotes['sets'].keys()):
                if('emoticons' in emotes['sets']['3'].keys()):
                    emotes = emotes['sets']['3']['emoticons']
    else:
        url = f'{API_URLS["ffz"]}/room/id/{channelId}'
        try:
            emotes = requests.get(url,params=None,headers=None).json()
        except:
            return None
        if(emotes is None):
            return None
        if('room' in emotes.keys()):
            if('set' in emotes['room'].keys()):
                emoteSetId = str(emotes['room']['set'])
        if('sets' in emotes.keys()):
            if(emoteSetId in emotes['sets'].keys()):
                if('emoticons' in emotes['sets'][emoteSetId].keys()):
                    emotes = emotes['sets'][emoteSetId]['emoticons']
    if(not emotes):
        return emoteSet
    if(isinstance(emotes, dict)):
        if('error' in emotes.keys()):
            return emoteSet 
    for i in range(0, len(emotes)):
        if(len(emotes[i]['urls']) == 1):
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/1')
        else:
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/4')
        emoteSet.append(emote)
    return emoteSet

def getHeaders():
    config = Config()
    return {"Authorization": f"Bearer {getOAuth(config.clientId, config.secretKey)}",
            "Client-Id": config.clientId}

def getOAuth(clientId, clientSecret):
    try:
        response = requests.post(
            OAUTH_URL + f'/token?client_id={clientId}&client_secret={clientSecret}&grant_type=client_credentials'
        )
        if(response is None):
            return None
        resp = response.json()
    except:
        return None
    if(resp is None):
        return None
    try:
        respKeys = resp.keys()
    except:
        return None
    if('access_token' in respKeys):
        return resp['access_token']
    return None
    
def getStreamInfo(channelName):
    url = f'{API_URLS["twitch"]}/streams?user_login={channelName}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
    except requests.ConnectionError:
        printException(channelName, 'Experienced a Connection Error.')
        return None
    except:
        return None
    if(resp is None):
        return None
    try:
        respKeys = resp.keys()
    except:
        return None
    if('error' in respKeys):
        return None
    if('data' in respKeys):
        if(len(resp['data']) == 0):
            return None
    else:
        return None
    return resp['data'][0]

def getTwitchEmoteById(channelId, emoteId, source) -> Emote:
    url = f'{API_URLS["twitch"]}/chat/emotes/global' if(source == 1) else f'{API_URLS["twitch"]}/chat/emotes?broadcaster_id={channelId}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
    except:
        return None
    if(resp is None):
        return None
    if('data' in resp.keys()):
        for emote in resp['data']:
            if(emoteId == emote['id']):
                return Emote(emoteId, emote['name'], emote['images']['url_4x'])

def getTwitchEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["twitch"]}/chat/emotes/global'
    else:
        url = f'{API_URLS["twitch"]}/chat/emotes?broadcaster_id={channelId}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
    except:
        return None
    try:
        if(resp is None):
            return None
        if('data' in resp.keys()):
            emotes = resp['data']
            if(not emotes):
                return None
            for i in range(0, len(emotes)):
                if('3.0' in emotes[i]['scale']):
                    if('animated' in emotes[i]['format']):
                        url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/animated/light/3.0'
                    else:
                        url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/static/light/3.0'
                else:
                    url = f'{CDN_URLS["twitch"]}/{emotes[i]["id"]}/static/light/1.0'
                emote = Emote(emotes[i]['id'], emotes[i]['name'], url)
                emoteSet.append(emote)
            return emoteSet
    except:
        if(not emoteSet):
            return None
        return emoteSet
    return emoteSet