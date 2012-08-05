from __future__ import with_statement

import json
import random
import os

import settings
import wrappers

from utils import MultiThreadObject

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

    BACK = 0
    NEXT = 1

    COMMANDS = {
        '': 'toggle_play',
        'n': 'next',
        'b': 'back',
        'p': 'toggle_pause',
        'u': 'up_vote',
        'd': 'down_vote',
        's': 'skip',
    }

    def __init__(self, db_file, wrapped_player):
        super(SmartPlayer, self).__init__()

        self.db_file = db_file
        self.wrapped_player = wrapped_player
        self.track_db = TrackDB(db_file)
        self._current_track = None
        self.voted_on_current_track = False
        self.paused = False
        self.accepted = {}
        self.undecided = {}
        self.dislike = {}
        self.playlist = []
        self.playlist_position = -1

        for track in wrapped_player.tracks:
            if track.excluded:
                continue

            # This is a track we haven't seen before, load it into the db
            if not track.key in self.track_db:
                self.track_db[track.key] = track.json

            # Split tracks between accepted and undecided
            if track.normalized_rating >= settings.ACCEPTED_RATING_THRESHOLD:
                self.accepted[track.key] = track
            elif track.normalized_rating >= settings.DISLIKE_THRESHOLD:
                self.undecided[track.key] = track
            else:
                self.dislike[track.key] = track

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
            self.up_vote()
        elif stopped_playing and (current >= time_for_down_vote or percentage >= amount_for_down_vote):
            self.down_vote()

    def up_vote(self):
        self.vote(self.current_track, self.UP_VOTE)
    def down_vote(self):
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

        if settings.DEBUG:
            print "rating: %d" % int(track_db_entry['rating'])

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


    def play(self, direction, skip=False):
        self.paused = False

        if not skip:
            self.check_for_vote(stopped_playing=True)

        if direction == self.BACK:
            if self.playlist_position <= 0:
                return

            self.playlist_position -= 1

        else:

            self.playlist_position += 1

            if self.playlist_position == len(self.playlist):

                # Decide if we are playing new music or not
                if random.random() <= settings.UNDECIDED_PLAY_RATE:
                    tracks = self.undecided
                else:
                    tracks = self.accepted

                next_track = tracks[random.choice(tracks.keys())]
                self.playlist.append(next_track)

        self.current_track = self.playlist[self.playlist_position]

        if settings.DEBUG:
            print "rating: %d" % self.track_db[self.current_track.key]['rating']

    def skip(self):
        self.play(self.NEXT, skip=True)

    def next(self):
        self.play(self.NEXT)

    def back(self):
        self.play(self.BACK)

    def toggle_play(self):
        if self.paused:
            self.toggle_pause()
        else:
            self.next()

    def toggle_pause(self):
        self.paused = not self.paused
        self.wrapped_player.toggle_pause()

    def stop(self):
        print "Closing..."
        self.wrapped_player.close()

    def tick(self):
        self.check_for_vote()

        # Need to distinguish between pausing the the underlying player
        # and a user pausing the script
        if not self.paused and self.wrapped_player.stopped:
            self.next()

    def set_current_track(self, track):
        self.voted_on_current_track = False
        self._current_track = track
        self.wrapped_player.play(track)
        print "Now Playing: %s" % track

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
        player = SmartPlayer(settings.DB_FILE, wrapped_player)
        player.start()
