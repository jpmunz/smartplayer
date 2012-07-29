from smartplayer import settings

class Track(object):

    def __init__(self, wrapped_track):
        self.wrapped_track = wrapped_track

    @property
    def name(self):
        NotImplemented()

    @property
    def artist(self):
        NotImplemented()

    @property
    def normalized_rating(self):
        NotImplemented()

    @property
    def comments(self):
        NotImplemented()

    @property
    def duration(self):
        NotImplemented()

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
            'rating': self.normalized_rating
        }

    def __str__(self):
        return "%s by %s" % (self.name, self.artist)
