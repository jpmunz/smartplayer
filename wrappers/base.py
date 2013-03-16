from smartplayer import settings

class Track(object):

    def __init__(self):
        pass

    @property
    def name(self):
        raise NotImplementedError

    @property
    def artist(self):
        raise NotImplementedError

    @property
    def initial_rating(self):
        raise NotImplementedError

    @property
    def comments(self):
        raise NotImplementedError

    @property
    def duration(self):
        raise NotImplementedError

    @property
    def excluded(self):
        return settings.EXCLUDE_STRING and settings.EXCLUDE_STRING in self.comments

    @property
    def key(self):
        return "%s::%s" % (self.name, self.artist)

    @property
    def json(self):
        return {
            'name': self.name,
            'artist': self.artist,
            'rating': self.initial_rating
        }

    def __str__(self):
        return "%s by %s" % (self.name, self.artist)

class PlayerWrapper(object):

    def __init__(self):
        super(PlayerWrapper, self).__init__()

    @property
    def tracks(self):
        raise NotImplementedError

    @property
    def position(self):
        raise NotImplementedError

    @property
    def stopped(self):
        raise NotImplementedError

    def play(self, track):
        raise NotImplementedError

    def toggle_pause(self):
        raise NotImplementedError

    def search(self, search_text):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False
