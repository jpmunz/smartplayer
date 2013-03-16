import os
import dbus
import eyed3
from base import Track, PlayerWrapper
from smartplayer import settings
from build_id3_db import generate_id3_db

class ID3Track(Track):

    def __init__(self, info, path):
        super(ID3Track, self).__init__()
        self.info = info
        self._path = path

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self.info['title'] or 'Unknown, path:%s' % self._path

    @property
    def artist(self):
        return self.info['artist'] or 'Unknown'

    @property
    def initial_rating(self):
        return 100

    @property
    def comments(self):
        return self.info['comments']

    @property
    def duration(self):
        return self.info['duration'] or 120

class ID3Wrapper(PlayerWrapper):

    def __init__(self):
        super(ID3Wrapper, self).__init__()

        music_path = getattr(settings, 'MUSIC_PATH', '~/Music')
        music_path = os.path.expanduser(music_path)
        self.id3_db = generate_id3_db(music_path, getattr(settings, 'ID3_DB_FILE', '.id3_db'), False)

        self._tracks = [ID3Track(self.id3_db[key], key) for key in self.id3_db]

    @property
    def tracks(self):
        return self._tracks

    def search(self, search_text):
        tokens = search_text.lower().split()

        candidates = self._tracks

        for token in tokens:
            remaining_candidates = []

            for track in candidates:
                if (track.artist and token in track.artist.lower()) or (track.name and token in track.name.lower()):
                    remaining_candidates.append(track)

            candidates = remaining_candidates

            if not remaining_candidates:
                break

        return candidates
