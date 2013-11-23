from __future__ import with_statement

import datetime
import json
import random
import os
import argparse
import settings
import wrappers

from tracks import display_track, find_tracks_file
from utils import MultiThreadObject, PersistedDict

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
        'f': 'search',
    }

    DIGIT_COMMAND = 'play_search_result'

    def __init__(self, db, wrapped_player, root_path=None, accepted_threshold=0, undecided_play_rate=10, verbose=False):
        super(SmartPlayer, self).__init__()

        self.wrapped_player = wrapped_player
        self.root_path = root_path
        self.track_db = db
        self.verbose = verbose
        self.accepted_threshold = accepted_threshold
        self.threshold_for_up_vote = settings.THRESHOLD_FOR_UP_VOTE
        self.threshold_for_down_vote = settings.THRESHOLD_FOR_DOWN_VOTE
        self.up_vote_for_accepted = settings.UP_VOTE_FOR_ACCEPTED
        self.up_vote_for_undecided = settings.UP_VOTE_FOR_UNDECIDED
        self.down_vote_for_accepted = settings.DOWN_VOTE_FOR_ACCEPTED
        self.down_vote_for_undecided = settings.DOWN_VOTE_FOR_UNDECIDED
        self.undecided_play_rate = undecided_play_rate / 100.0
        self._current_track = None
        self.voted_on_current_track = False
        self.paused = False
        self.accepted = {}
        self.undecided = {}
        self.excluded = {}
        self.playlist = []
        self.playlist_position = -1
        self.search_results = []

        for track_info in self.track_db.values():
            tracks = self.accepted if track_info.get('rating', 0) >= accepted_threshold else self.undecided
            groups = track_info.get('groups', [])
            if any(exclusion in groups for exclusion in settings.EXCLUDED_SHUFFLE_GROUPS):
                tracks = self.excluded

            tracks[track_info['pk']] = track_info

        if self.accepted:
            self.next()
        else:
            print "No acceptable tracks found"
            self.stop()

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
        total = self.current_track['duration']
        percentage = (current / float(total))

        # Voting thresholds
        time_for_up_vote, amount_for_up_vote = self.threshold_for_up_vote
        time_for_down_vote, amount_for_down_vote = self.threshold_for_down_vote

        # Decide if we should vote on the song yet
        if current >= time_for_up_vote or percentage >= amount_for_up_vote:
            self.up_vote()
        elif stopped_playing and (current >= time_for_down_vote or percentage >= amount_for_down_vote):
            self.down_vote()

    def up_vote(self):
        self.vote(self.current_track, self.UP_VOTE)
    def down_vote(self):
        self.vote(self.current_track, self.DOWN_VOTE)

    def log(self, msg):
        if self.verbose:
            print msg

    def vote(self, track, kind):
        '''
        Update the track's rating in the DB based on whether we are up or down voting.

        Additionally might need to switch it from undecided to accepted if we crossed the threshold
        '''

        self.voted_on_current_track = True

        # Get correct increment for the vote
        if kind == self.UP_VOTE:
            accepted_change, undecided_change = self.up_vote_for_accepted, self.up_vote_for_undecided
            self.log('up voting')
        else:
            accepted_change, undecided_change = self.down_vote_for_accepted, self.down_vote_for_undecided
            self.log('down voting')

        # Update the tracks rating and save to the DB
        track['rating'] += accepted_change if track['pk'] in self.accepted else undecided_change
        self.track_db.save()
        self.log("rating: %d" % int(track['rating']))

        # Move the track if it has crossed the threshold for being Accepted
        from_group = None
        to_group = None
        if track['rating'] >= self.accepted_threshold and track['pk'] not in self.accepted:
            from_group = self.undecided
            to_group = self.accepted
            self.log('promoting track to accepted')
        elif track['rating'] < self.accepted_threshold and track['pk'] not in self.undecided:
            from_group = self.accepted
            to_group = self.undecided
            self.log('demoting track to undecided')

        if from_group and to_group:
            del from_group[track['pk']]
            to_group[track['pk']] = track

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
                if random.random() <= self.undecided_play_rate:
                    tracks = self.undecided

                    if not tracks:
                        tracks = self.accepted
                else:
                    tracks = self.accepted

                next_track = tracks[random.choice(tracks.keys())]
                self.playlist.append(next_track)

        self.current_track = self.playlist[self.playlist_position]
        self.log("rating: %d" % self.current_track.get('rating', 0))

    def play_track(self, track):
        self.playlist.append(track)
        self.skip()

    def skip(self):
        skipped_track = self.current_track
        self.play(self.NEXT, skip=True)
        self.incr_skip_count(skipped_track)

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

    def search(self, search_text):
        if not search_text:
            return

        tokens = search_text.lower().split()

        candidates = self.track_db.values()

        for token in tokens:
            remaining_candidates = []

            for track in candidates:
                if any(track.get(field) and token in track[field].lower() for field in ['artist', 'album', 'title']):
                    remaining_candidates.append(track)

            candidates = remaining_candidates

            if not remaining_candidates:
                break

        self.search_results = remaining_candidates

        for i, track in enumerate(self.search_results):
            print "%d. %s" % (i + 1, display_track(track))

    def play_search_result(self, number):
        if len(self.search_results) >= number:
            self.play_track(self.search_results[number - 1])
        else:
            print "Invalid search result index: %d" % number

    def stop(self):
        print "Closing..."
        self.wrapped_player.close()

    def tick(self):
        self.check_for_vote()

        # Need to distinguish between pausing the the underlying player
        # and a user pausing the script
        if not self.paused and self.wrapped_player.stopped:
            finished_track = self.current_track
            self.next()
            self.incr_listen_count(finished_track)

    def incr_listen_count(self, track):
        track['listen_count'] = track.get('listen_count', 0) + 1
        track['date_played'] = datetime.datetime.now().strftime(settings.DATE_FORMAT)
        self.track_db.save()

    def incr_skip_count(self, track):
        track['skip_count'] = track.get('skip_count', 0) + 1
        self.track_db.save()

    def set_current_track(self, track):
        self.voted_on_current_track = False
        self._current_track = track
        self.wrapped_player.play(os.path.join(self.root_path, track['file_path']))
        print "Now Playing: %s" % display_track(track)

    def get_current_track(self):
        return self._current_track

    current_track = property(get_current_track, set_current_track)


def play(path, player=None, accepted_threshold=None, undecided_play_rate=None, verbose=False):
    wrapper_cls = getattr(wrappers, player, None)

    if not wrapper_cls:
        print "Wrapper not found: %s" % player
        return

    with wrapper_cls() as wrapped_player:
        tracks_file = find_tracks_file(path)
        root_path = tracks_file.rpartition('/')[0]

        player = SmartPlayer(PersistedDict(tracks_file), wrapped_player, root_path=root_path, accepted_threshold=accepted_threshold, undecided_play_rate=undecided_play_rate, verbose=verbose)

        player.start()
