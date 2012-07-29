from __future__ import with_statement

import json
import random
import os

import settings
import wrappers

from utils import MultiThreadObject

DB_FILE = '.tracks'

class TrackDB(dict):

    def __init__(self, db_file):
        self.db_file = db_file

        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                db_data = f.read()

                if db_data:
                    self.update(json.loads(db_data))

    def save(self):
        with open(self.db_file, 'w+') as f:
            f.write(json.dumps(self))

class SmartPlayer(MultiThreadObject):

    UP_VOTE = 1
    DOWN_VOTE = 0

    COMMANDS = {
        '': 'next',
        'p': 'toggle_pause',
    }

    def __init__(self, db_file, wrapped_player):
        super(SmartPlayer, self).__init__()

        self.db_file = db_file
        self.wrapped_player = wrapped_player
        self.track_db = TrackDB(db_file)
        self.current_track = None
        self.voted_on_current_track = False
        self.accepted = {}
        self.undecided = {}

        for track in wrapped_player.tracks:
            if track.excluded:
                continue

            # This is a track we haven't seen before, load it into the db
            if not track.key in self.track_db:
                self.track_db[track.key] = track.json

            # Split tracks between accepted and undecided
            if track.normalized_rating >= settings.ACCEPTED_RATING_THRESHOLD:
                self.accepted[track.key] = track
            else:
                self.undecided[track.key] = track

        self.track_db.save()

        self.next()

    def check_for_vote(self, stopped_playing=False):
        '''
        Looks at how far into the current track we are. 
        
        Up vote it if we've listened to enough of it to qualify. Otherwise if the song 
        stopped playing and we played it long enough to not consider it a skip we
        need to down vote it.
        '''

        if not self.current_track or self.voted_on_current_track:
            return

        # Calculate how far into the song we are
        current = self.wrapped_player.position
        total = self.current_track.duration
        percentage = (current / float(total))

        # Voting thresholds
        time_for_up_vote, amount_for_up_vote = settings.THRESHOLD_FOR_UP_VOTE
        time_for_down_vote, amount_for_down_vote = settings.THRESHOLD_FOR_DOWN_VOTE

        # Decide if we should vote on the song yet
        if current >= time_for_up_vote or percentage >= amount_for_up_vote:
            self.vote(self.current_track, self.UP_VOTE)
        elif stopped_playing and (current >= time_for_down_vote or percentage >= amount_for_down_vote):
            self.vote(self.current_track, self.DOWN_VOTE)

    def vote(self, track, kind):
        '''
        Update the track's rating in the DB based on whether we are up or down voting.

        Additionally might need to switch it from undecided to accepted if we crossed the threshold
        '''

        self.voted_on_current_track = True

        # Get correct increment for the vote
        if kind == self.UP_VOTE:
            accepted_change, undecided_change = settings.UP_VOTE_FOR_ACCEPTED, settings.UP_VOTE_FOR_UNDECIDED
            if settings.DEBUG:
                print 'up voting'
        else:
            accepted_change, undecided_change = settings.DOWN_VOTE_FOR_ACCEPTED * -1, settings.DOWN_VOTE_FOR_UNDECIDED * -1
            if settings.DEBUG:
                print 'down voting'

        # Update the tracks rating and save to the DB
        track_db_entry = self.track_db[track.key]
        track_db_entry['rating'] += accepted_change if track.key in self.accepted else undecided_change
        self.track_db.save()

        # Move the track if it has crossed the threshold for being Accepted
        if track_db_entry['rating'] < settings.ACCEPTED_RATING_THRESHOLD and track.key in self.accepted:
           self.accepted.pop(track.key)
           self.undecided[track.key] = track

           if settings.DEBUG:
               print 'demoting track to undecided'

        elif track_db_entry['rating'] >= settings.ACCEPTED_RATING_THRESHOLD and track.key in self.undecided:
           self.undecided.pop(track.key)
           self.accepted[track.key] = track

           if settings.DEBUG:
               print 'promoting track to accepted'

    def next(self):
        self.check_for_vote(stopped_playing=True)

        # Decide if we are playing new music or not
        if random.random() <= settings.UNDECIDED_PLAY_RATE:
            tracks = self.undecided
            if settings.DEBUG:
                'picking an undecided track'
        else:
            tracks = self.accepted

        # Play random track
        self.current_track = tracks[random.choice(tracks.keys())]

        self.wrapped_player.play(self.current_track)

        print "Now Playing: %s" % self.current_track

    def toggle_pause(self):
        self.wrapped_player.toggle_pause()

    def stop(self):
        print "Closing..."
        self.wrapped_player.close()

    def tick(self):
        self.check_for_vote()

        if self.wrapped_player.stopped:
            self.next()

    def set_current_track(self, track):
        self.voted_on_current_track = False
        self._current_track = track

    def get_current_track(self):
        return self._current_track

    current_track = property(get_current_track, set_current_track)

if __name__ == '__main__':

    wrapper_cls = getattr(wrappers, settings.WRAPPER, None)

    if not wrapper_cls:
        print "Wrapper not found: %s" % settings.WRAPPER
        exit()

    print "Loading..."
    with wrapper_cls() as wrapped_player:
        player = SmartPlayer(DB_FILE, wrapped_player)
        player.start()
