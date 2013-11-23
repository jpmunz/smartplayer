import time
from win32com import client
from ..base import Track, PlayerWrapper

class ItunesWrapper(PlayerWrapper):
    STOPPED_STATE = 0
    SEARCH_ALL_FIELDS = 0

    def __init__(self):
        super(ItunesWrapper, self).__init__()
        self.itunes = client.Dispatch('iTunes.Application')

    @property
    def position(self):
        return self.itunes.PlayerPosition

    @property
    def stopped(self):
        return self.itunes.PlayerState == self.STOPPED_STATE

    def play(self, track):
        raise NotImplementedError # TODO Play from file
        attempts = 0
        while True:
            try:
                track.wrapped_track.Play()
                break
            except Exception, e:
                print "Failed on trying to play %s, error:%s" % (track.name, e)

                attempts += 1
                time.sleep(1)
                if attempts >= 3:
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
