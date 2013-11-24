DEBUG = True
WRAPPER = 'ExaileWrapper'
MUSIC_PATH = '/home/jon/Music/iTunes/'
ID3_DB_FILE = '/home/jon/code/smartplayer/.id3_db'
DB_FILE = '/home/jon/Dropbox/.tracks'

ID3_TAGS_TO_REPORT_MISSING = ['artist', 'album', 'title']
FILE_TYPES_TO_LOAD = ['wma', 'm4a', 'mp3', 'mp4']

ACCEPTED_THRESHOLD = 100

UNDECIDED_PLAY_RATE = .1

UP_VOTE_FOR_ACCEPTED = 5
UP_VOTE_FOR_UNDECIDED = 50

DOWN_VOTE_FOR_ACCEPTED = -10
DOWN_VOTE_FOR_UNDECIDED = -30


THRESHOLD_FOR_UP_VOTE = (120, .8) # (seconds, percentage)
THRESHOLD_FOR_DOWN_VOTE = (10, .1)


