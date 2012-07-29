from mock import Mock
from wrappers.base import Track

class MockTrack(Track):
    def __init__(self, name, artist, rating, comments, duration=60):
        self._name = name
        self._artist = artist
        self._comments = comments
        self.rating = rating
        self._duration = duration

    @property
    def name(self):
        return self._name

    @property
    def artist(self):
        return self._artist

    @property
    def comments(self):
        return self._comments

    @property
    def duration(self):
        return self._duration

    @property
    def normalized_rating(self):
        return self.rating

class MockWrapper(Mock):

    def __init__(self, tracks):
        super(MockWrapper, self).__init__()
        self._tracks = tracks
        self._position = 0

    @property
    def tracks(self):
        return self._tracks

    @property
    def position(self):
        return self._position

    def play(self, track):
        pass

    def pause(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False
