import os
import dbus
import time
from ..base import PlayerWrapper

def retry(max_attempts):
    '''
    DBus calls can be unreliable, every now and then one will just fail
    to execute, this attempts a function call multiple times before
    giving up
    '''
    def wrap(func):
        def wrapped_func(*args, **kwargs):
            attempts = 0

            while True:
                try:
                    return func(*args, **kwargs)
                    break
                except Exception, e:
                    attempts += 1
                    if attempts >= max_attempts:
                        break
                    time.sleep(1)

        return wrapped_func
    return wrap

class ExaileWrapper(PlayerWrapper):

    def __init__(self):
        super(ExaileWrapper, self).__init__()
        bus = dbus.SessionBus()
        bus.start_service_by_name('org.exaile.Exaile')
        obj = bus.get_object('org.exaile.Exaile', '/org/exaile/Exaile')

        self.media_player = dbus.Interface(obj, 'org.exaile.Exaile')

    @property
    @retry(max_attempts=10)
    def position(self):
        minute, second = self.media_player.CurrentPosition().split(':')
        return (int(minute) * 60) + int(second)

    @property
    @retry(max_attempts=10)
    def stopped(self):
        return 'Not playing' in self.media_player.Query()

    @retry(max_attempts=10)
    def play(self, file_path):
        self.media_player.Stop()
        self.media_player.PlayFile(file_path)
        self.media_player.StopAfterCurrent()

    @retry(max_attempts=10)
    def toggle_pause(self):
        self.media_player.PlayPause()

    def close(self):
        os.system("killall -9 exaile")
