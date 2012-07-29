import time
from win32com import client

from wrappers.base import Track

class ItunesTrack(Track):

    def __init__(self, wrapped_track):
        super(ItunesTrack, self).__init__(wrapped_track)

    @property
    def name(self):
        return self.wrapped_track.Name

    @property
    def artist(self):
        return self.wrapped_track.Artist

    @property
    def normalized_rating(self):
        return (self.wrapped_track.Rating / 60.0) * 100

    @property
    def comments(self):
        return self.wrapped_track.Comment

    @property
    def duration(self):
        return self.wrapped_track.Duration

class ItunesWrapper(object):

    STOPPED_STATE = 0

    def __init__(self):
        self.itunes = client.Dispatch('iTunes.Application')

    @property
    def tracks(self):
        return [ItunesTrack(track) for track in self.itunes.LibraryPlaylist.Tracks]

    @property
    def position(self):
        return self.itunes.PlayerPosition

    @property
    def stopped(self):
        return self.itunes.PlayerState == self.STOPPED_STATE

    def play(self, track):
        try:
            track.wrapped_track.Play()
        except Exception, e:
            print "Failed on trying to play %s, error:%s" % (track.name, e)
            raise

    def toggle_pause(self):
        self.itunes.PlayPause()

    def close(self):
        # What's happening here is that Quit() doesn't reliably close
        # the application and its return is always None regardless of
        # success or failure, so I keep calling it every second until
        # the COM object throws an exception on trying to perform
        # the call which I take to mean that it finally closed

        attempts = 0
        while True:
            try:
                if attempts > 10:
                    break

                self.itunes.Quit()
                attempts += 1
                time.sleep(1)
            except Exception:
                break

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False
