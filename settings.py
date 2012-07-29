DEBUG = False

WRAPPER = 'ItunesWrapper'

DB_FILE = '.tracks'

ACCEPTED_RATING_THRESHOLD = 100

EXCLUDE_STRING = 'exclude' # searched for in the 'Comments' field
UNDECIDED_PLAY_RATE = .2

UP_VOTE_FOR_ACCEPTED = 5
UP_VOTE_FOR_UNDECIDED = 50

DOWN_VOTE_FOR_ACCEPTED = 10
DOWN_VOTE_FOR_UNDECIDED = 30


THRESHOLD_FOR_UP_VOTE = (120, .8) # (seconds, percentage)
THRESHOLD_FOR_DOWN_VOTE = (15, .1)

try:
    from localsettings import *
except:
    pass
