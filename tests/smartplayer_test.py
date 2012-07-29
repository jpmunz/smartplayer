import unittest
from mock import patch

import json

from smartplayer import settings
from smartplayer.smartplayer import SmartPlayer
from smartplayer.wrappers.mockwrapper import MockWrapper, MockTrack


class TestSmartPlayer(unittest.TestCase):

    def setUp(self):
        self.db_file = '.tracks_test'

        self.track1 = MockTrack("A", "foo", 110, "shuffle")
        self.track2 = MockTrack("B", "foo", 0, "exclude")
        self.track3 = MockTrack("C", "foo", 40, "shuffle")
        self.track4 = MockTrack("D", "foo", 100, "shuffle")
        self.track5 = MockTrack("E", "foo", 90, "exclude")

        self.tracks = [self.track1, self.track2, self.track3, self.track4, self.track5]

        self.wrapper = MockWrapper(self.tracks)

    def teardown(self):
        pass

    def test_rating_threshold(self):
        settings.ACCEPTED_RATING_THRESHOLD = 100

        player = SmartPlayer(self.db_file, self.wrapper)

        self.assertEqual(len(player.accepted), 2)
        self.assertTrue(self.track1.key in player.accepted)
        self.assertTrue(self.track4.key in player.accepted)

        self.assertEqual(len(player.undecided), 1)
        self.assertTrue(self.track3.key in player.undecided)

    def test_saving_db(self):
        initial = {
            'A::foo': {'rating': 2000},
            'Z::bar': {'rating': 20},
        }

        with open(self.db_file, 'w+') as f:
            f.write(json.dumps(initial))

        self.player = SmartPlayer(self.db_file, self.wrapper)

        # DB should have loaded anything already in the file
        self.assertEqual(self.player.track_db['Z::bar']['rating'], 20)

        # If it's already in the DB, shouldn't be overwritten
        self.assertEqual(self.player.track_db['A::foo']['rating'], 2000)

        # DB should be saved back after initialization
        with open(self.db_file, 'r') as f:
            saved_data = json.loads(f.read())

            for track in self.tracks[1:]:
                if not track.excluded:
                    self.assertEqual(saved_data[track.key], track.json)

    def test_voting_scenarios(self):
        track = MockTrack("F", "foo", 110, "shuffle", duration=100)
        wrapper = MockWrapper([track])

        settings.UNDECIDED_PLAY_RATE = 0 # Force the accepted track to be picked
        player = SmartPlayer(self.db_file, wrapper)
        player.current_track = track

        settings.THRESHOLD_FOR_DOWN_VOTE = (20, .1)
        settings.THRESHOLD_FOR_UP_VOTE = (60, .8)

        settings.ACCEPTED_RATING_THRESHOLD = 100

        # Skipped too quickly for down vote 
        self.voting_scenario(player, position=5, stopped=True, expected_rating=110, expected_type='accepted')

        # Don't down vote if it's still playing
        self.voting_scenario(player, position=10, stopped=False, expected_rating=110, expected_type='accepted')

        # Down vote if played more than skip time and percentage thresholds
        settings.DOWN_VOTE_FOR_ACCEPTED = 25
        self.voting_scenario(player, position=10, stopped=True, expected_rating=85, expected_type='undecided')

        settings.DOWN_VOTE_FOR_UNDECIDED = 30
        self.voting_scenario(player, position=20, stopped=True, reset_vote=False, expected_rating=85, expected_type='undecided')
        self.voting_scenario(player, position=20, stopped=True, expected_rating=55, expected_type='undecided')

        # Up vote if played more than accepted time and percentage thresholds
        settings.UP_VOTE_FOR_UNDECIDED = 50
        self.voting_scenario(player, position=60, expected_rating=105, expected_type='accepted')

        settings.UP_VOTE_FOR_ACCEPTED = 5
        self.voting_scenario(player, position=80, expected_rating=110, expected_type='accepted')

    def voting_scenario(self, player, reset_vote=True, stopped=False, position=None, expected_rating=None, expected_type=None):
        player.wrapped_player._position = position

        if reset_vote:
            player.current_track = player.current_track

        player.check_for_vote(stopped_playing=stopped)
        self.assertEqual(player.track_db[player.current_track.key]['rating'], expected_rating)

        if expected_type == 'accepted':
            self.assertTrue(player.current_track.key in player.accepted)
            self.assertFalse(player.current_track.key in player.undecided)
        else:
            self.assertTrue(player.current_track.key in player.undecided)
            self.assertFalse(player.current_track.key in player.accepted)

    def test_next_song(self):
        accepted_track = MockTrack("F", "foo", 110, "shuffle")
        undecided_track = MockTrack("R", "foo", 90, "shuffle")

        wrapper = MockWrapper([accepted_track, undecided_track])

        settings.UNDECIDED_PLAY_RATE = .2

        with patch('smartplayer.smartplayer.random') as random:
            random.choice = lambda seq: seq[0]

            random.random.return_value = .2
            player = SmartPlayer(self.db_file, wrapper)
            self.assertEqual(player.current_track, undecided_track)

            random.random.return_value = .5
            player.next()
            self.assertEqual(player.current_track, accepted_track)
