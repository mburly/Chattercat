import pyfiglet


CONFIG_NAMES = { 'op':'conf.ini',
                 'dwh':'wh.ini' }
CHANNELS = 'channels.txt'
SERVER = 'irc.chat.twitch.tv'
PORT = 6667
ADDRESS = (SERVER, PORT)
BAD_FILE_CHARS = ['\\','/',':','*','?','"','<','>','|']
CONFIG_SECTIONS = { 'db':'db',
                    'twitch':'twitch' }
DB_VARIABLES = { 'host':'host',
                 'user':'user',
                 'password':'password' }
TWITCH_VARIABLES = { 'nickname':'nickname',
                     'token':'token',
                     'secret_key':'secret_key',
                     'client_id':'client_id' }
DIRS = { 'emotes':'emotes', 
         'twitch':'emotes/twitch', 
         'bttv':'emotes/bttv', 
         'ffz':'emotes/ffz',
         '7tv':'emotes/7tv',
         'pictures':'pictures',
         'pictures_archive':'pictures/archive' }
API_URLS = { 'twitch':'https://api.twitch.tv/helix',
             'ffz':'https://api.frankerfacez.com/v1',
             'bttv':'https://api.betterttv.net/3/cached',
             '7tv':'https://7tv.io/v3' }
CDN_URLS = { 'twitch':'https://static-cdn.jtvnw.net/emoticons/v2',
             'ffz':'https://cdn.frankerfacez.com/emote',
             'bttv':'https://cdn.betterttv.net/emote',
             '7tv':'https://cdn.7tv.app/emote/#/4x.webp' }
OAUTH_URL = 'https://id.twitch.tv/oauth2'
SERVER_URL = 'tmi.twitch.tv'
COLORS = { 'clear':'\033[0m',
           'bold_blue':'\033[1;34m',
           'bold_purple':'\033[1;35m',
           'hi_green':'\033[0;92m',
           'hi_red':'\033[0;91m',
           'hi_yellow':'\033[93m' }
BANNER = f'{COLORS["bold_purple"]}{pyfiglet.figlet_format("Chattercat", font="speed")}{COLORS["clear"]}'
VERSION = '1.1'
EMOTE_TYPES = ['twitch','subscriber','ffz','ffz_channel','bttv','bttv_channel','7tv','7tv_channel']
DEBUG_MESSAGES = { 'set_emote':'Setting emote:',
                   'inactive':'now inactive.',
                   'reactivated':'now reactivated.' }
ERROR_MESSAGES = { 'host':'Unable to connect to host. Likely lost internet connection.',
                   'channel':'Channel not found.',
                   'database':'Unable to connect to database.',
                   'directory':'Unable to create emote directories.',
                   'offline':'Stream offline. Please try another channel or try again later.',
                   'config':'Bad value(s) provided in the configuration file. Please check and update config.ini.',
                   'connection':'No internet connection found. Please try again.',
                   'no_streams':'No streams provided. Please add at least one channel to streams.txt',
                   'invalid_streams':'No valid streams provided. Please add at least one valid channel name in streams.txt',
                   'connection':'Experienced a Connection Error.' }
STATUS_MESSAGES = { 'downloading':'Downloading channel emotes...',
                    'updates':'Checking for emote updates...',
                    'updates_complete':'Emote update check complete.',
                    'validating':'Validating Twitch channels...',
                    'channel_validated':'Channel validated.',
                    'validating_complete':'Channel validation complete.',
                    'dwh_export_start': 'Beginning export to Data Warehouse.',
                    'dwh_export_complete': 'Export to Data Warehouse complete.' }
TIMERS = { 'sleep':15,
           'live':1,
           'socket':5 }
EXECUTION_HANDLER_CODES = { 'start':'A',
                            'end':'E' }
ADMIN_DB_NAME = 'cc_housekeeping'
DB_PREFIX = 'cc_'
DWH_DB_PREFIX = 'ccdwh_'
TRUNCATE_LIST = ['Messages', 'Chatters', 'Segments', 'Sessions', 'Games']
TWITCH_CHANNEL_DATA = ['id', 'broadcaster_type', 'description', 'profile_image_url',
                       'offline_image_url', 'view_count', 'created_at']
CHANNEL_PROPERTIES = ['channelId', 'type', 'description', 'profileImageUrl',
                      'offlineImageUrl', 'viewCount', 'created']
TWITCH_STREAM_DATA = ['id', 'user_id', 'game_id', 'game_name', 'title',
                      'viewer_count', 'started_at', 'thumbnail_url', 'tags',
                      'is_mature']
STREAM_PROPERTIES = ['streamId', 'channelId', 'gameId', 'gameName', 'title',
                     'viewerCount', 'streamStart', 'thumbnailUrl', 'tags',
                     'isMature']