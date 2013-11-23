DEBUG = False
ID3_TAGS = ['artist', 'album', 'title']

WRAPPER = 'ItunesWrapper'

ACCEPTED_THRESHOLD = 100

UNDECIDED_PLAY_RATE = .1

UP_VOTE_FOR_ACCEPTED = 5
UP_VOTE_FOR_UNDECIDED = 50

DOWN_VOTE_FOR_ACCEPTED = -10
DOWN_VOTE_FOR_UNDECIDED = -30


THRESHOLD_FOR_UP_VOTE = (120, .8) # (seconds, percentage)
THRESHOLD_FOR_DOWN_VOTE = (10, .1)

try:
    from localsettings import *
except:
    pass
