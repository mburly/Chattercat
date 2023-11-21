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

def getAllChannelEmotes(channelName):
    channelId = getChannelId(channelName)
    channelEmotes = {}
    channelEmotes[EMOTE_TYPES[0]] = getTwitchEmotes()
    channelEmotes[EMOTE_TYPES[1]] = getTwitchEmotes(channelName)
    channelEmotes[EMOTE_TYPES[2]] = getFFZEmotes()
    channelEmotes[EMOTE_TYPES[3]] = getFFZEmotes(channelId)
    channelEmotes[EMOTE_TYPES[4]] = getBTTVEmotes()
    channelEmotes[EMOTE_TYPES[5]] = getBTTVEmotes(channelId)
    try:
        channelEmotes[EMOTE_TYPES[6]] = get7TVEmotes()
    except Exception as e:
        utils.printInfo(channelName, f'1: {e}')
    try:
        channelEmotes[EMOTE_TYPES[7]] = get7TVEmotes(channelId)
    except Exception as e:
        utils.printInfo(channelName, f'2: {e}')
    return channelEmotes

def get7TVEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["7tv"]}/emote-sets/62cdd34e72a832540de95857'
        emotes = requests.get(url,params=None,headers=None).json()['emotes']
        for emote in emotes:
            emoteSet.append(Emote(emote['id'], emote['name'], f"{CDN_URLS['7tv'].replace('#', emote['id'])}"))
    else:
        url = f'{API_URLS["7tv"]}/users/twitch/{channelId}'
        try:
            emotes = requests.get(url,params=None,headers=None).json()['emote_set']['emotes']
        except:
            return emoteSet
        for emote in emotes:
            emoteSet.append(Emote(emote['id'], emote['name'], CDN_URLS['7tv'].replace('#', emote['id'])))
    return emoteSet

def getBTTVEmoteById(channelId, emoteId) -> Emote:
    url = f'{API_URLS["bttv"]}/users/twitch/{channelId}'
    try:
        emotes = requests.get(url,params=None,headers=None).json()['sharedEmotes']
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')
        emotes = requests.get(url,params=None,headers=None).json()['channelEmotes']
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')
        # Still not found, check BTTV Global emotes
        url = f'{API_URLS["bttv"]}/emotes/global'
        emotes = requests.get(url,params=None,headers=None).json()
        for emote in emotes:
            if(emote['id'] == emoteId):
                return Emote(emoteId, emote['code'], f'{CDN_URLS["bttv"]}/{emoteId}/3x.{emote["imageType"]}')
    except Exception as e:
        utils.printInfo(channelId, f'Exception in getBTTVEmoteById: {e}')
        return None

def getBTTVEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["bttv"]}/emotes/global'
        emotes = requests.get(url,params=None,headers=None).json()
        for i in range(0, len(emotes)):
            emoteSet.append(Emote(emotes[i]['id'], emotes[i]['code'], f'{CDN_URLS["bttv"]}/{emotes[i]["id"]}/3x.{emotes[i]["imageType"]}'))
    else:
        url = f'{API_URLS["bttv"]}/users/twitch/{channelId}'
        emotes = requests.get(url,params=None,headers=None).json()
        try:
            channelEmotes = emotes['channelEmotes']
        except Exception as e:
            utils.printInfo(channelId, f'Exception in getBTTVEmotes: {e}')
            return None
        if(len(channelEmotes) != 0):
            for i in range(0, len(channelEmotes)):
                emoteSet.append(Emote(channelEmotes[i]['id'], channelEmotes[i]['code'], f'{CDN_URLS["bttv"]}/{channelEmotes[i]["id"]}/3x.{channelEmotes[i]["imageType"]}'))
        try:
            sharedEmotes = emotes['sharedEmotes']
        except:
            if(emoteSet == []):
                return None
            return emoteSet
        if(len(sharedEmotes) != 0):
            for i in range(0, len(sharedEmotes)):
                emoteSet.append(Emote(sharedEmotes[i]['id'], sharedEmotes[i]['code'], f'{CDN_URLS["bttv"]}/{sharedEmotes[i]["id"]}/3x.{sharedEmotes[i]["imageType"]}'))
    return emoteSet

def getChannelId(channelName):
    try:
        return int(getChannelInfo(channelName)['id'])
    except Exception as e:
        utils.printInfo(channelName, f'Exception in getChannelId: {e}')
        return None

def getChannelInfo(channelName):
    url = f'{API_URLS["twitch"]}/users?login={channelName}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
        if('error' in resp.keys()):
            return None
        return resp['data'][0]
    except Exception as e:
        utils.printInfo(channelName, f'Exception in getChannelInfo: {e}')
        return None

def getChatterColor(chatterName):
    userId = getChannelId(chatterName)
    url = f'{API_URLS["twitch"]}/chat/color?user_id={userId}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
        if('error' in resp.keys()):
            return None
        return resp['data'][0]['color']
    except:
        return None

def getEmoteById(channelId, emoteId, source) -> Emote:
    if(source == 1 or source == 2):
        return getTwitchEmoteById(channelId, emoteId, source)
    elif(source == 3 or source == 4):
        return getFFZEmoteById(emoteId)
    else:
        return getBTTVEmoteById(channelId, emoteId)

def getFFZEmoteById(emoteId) -> Emote:
    url = f'{API_URLS["ffz"]}/emote/{emoteId}'
    try:
        emote = requests.get(url,params=None,headers=None).json()
        if(len(emote['emote']['urls']) == 1):
            return Emote(emoteId, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emoteId}/1')
        else:
            return Emote(emoteId, emote['emote']['name'], f'{CDN_URLS["ffz"]}/{emoteId}/4')
    except Exception as e:
        utils.printInfo(emoteId, f'Exception in getFFZEmoteById: {e}')
        return None

def getFFZEmotes(channelId=None):
    emoteSet = []
    if(channelId is None):
        url = f'{API_URLS["ffz"]}/set/global'
        emotes = requests.get(url,params=None,headers=None).json()
        emotes = emotes['sets']['3']['emoticons']
    else:
        url = f'{API_URLS["ffz"]}/room/id/{channelId}'
        emotes = requests.get(url,params=None,headers=None).json()
        try:
            emoteSetId = str(emotes['room']['set'])
        except:
            return None
        emotes = emotes['sets'][emoteSetId]['emoticons']
    if(emotes == []):
        return None
    for i in range(0, len(emotes)):
        if(len(emotes[i]['urls']) == 1):
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/1')
        else:
            emote = Emote(emotes[i]['id'], emotes[i]['name'], f'{CDN_URLS["ffz"]}/{emotes[i]["id"]}/4')
        emoteSet.append(emote)
    return emoteSet

def getHeaders():
    config = utils.Config()
    return {"Authorization": f"Bearer {getOAuth(config.clientId, config.secretKey)}",
            "Client-Id": config.clientId}

def getOAuth(clientId, clientSecret):
    try:
        response = requests.post(
            constants.OAUTH_URL + f'/token?client_id={clientId}&client_secret={clientSecret}&grant_type=client_credentials'
        )
        return response.json()['access_token']
    except Exception as e:
        utils.printInfo(None, f'Exception in getOAuth: {e}')
        return None

def getStreamInfo(channelName):
    url = f'{API_URLS["twitch"]}/streams?user_login={channelName}'
    try:
        resp = requests.get(url,params=None,headers=getHeaders()).json()
    except requests.ConnectionError:
        utils.printInfo(channelName, f'getStreamInfo (connection error)')
        return None
    respKeys = resp.keys()
    if('error' in respKeys):
        utils.printInfo(channelName, resp['error'])
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
        emotes = requests.get(url,params=None,headers=getHeaders()).json()['data']
        for emote in emotes:
            if(emoteId == emote['id']):
                return Emote(emoteId, emote['name'], emote['images']['url_4x'])
    except Exception as e:
        utils.printInfo(channelId, f'Exception in getTwitchEmoteById: {e}')
        return None

def getTwitchEmotes(channelName=None):
    emoteSet = []
    if(channelName is None):
        url = f'{API_URLS["twitch"]}/chat/emotes/global'
    else:
        url = f'{API_URLS["twitch"]}/chat/emotes?broadcaster_id={getChannelId(channelName)}'
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
            emoteSet.append(emote)
        return emoteSet
    except Exception as e:
        utils.printInfo(channelName, f'Exception in getTwitchEmotes: {e}')
        return None
