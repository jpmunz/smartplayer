import os
from tracks import get_track_key
from utils import PersistedDict, find_tracks_file

def find_tracks_file(path):
    path = os.path.abspath(os.path.expanduser(path))

    for file_name in os.listdir(path):
        if file_name == '.tracks':
            return os.path.join(path, '.tracks')

    parent_path = os.path.abspath(os.path.join(path, os.pardir))
    if parent_path == path:
        # Reach the root
        raise Exception("No .tracks file found")
    else:
        return find_tracks_file(parent_path)

def get_track_info(path):
    try:
        tracks_file = find_tracks_file(path)
    except Exception, e:
        tracks_file = None
        print e

    if tracks_file:
        db = PersistedDict(tracks_file)
        for track_info in db.values():
            yield track_info

def report_duplicates(path):
    id3_info = {}
    for track_info in get_track_info(path):
        key = get_track_key(track_info)

        if key in id3_info:
            print "'%s' duplicates '%s'" % (track_info['pk'], id3_info[key])
        else:
            id3_info[key] = track_info['pk']

def report_missing(path, tags=None):
    if tags is None:
        tags = []

    for track_info in get_track_info(path):
        missing_fields = [tag for tag in tags if not track_info.get(tag)]
        if missing_fields:
            print "%s\tMissing fields: %s" % (track_info['pk'], ', '.join(missing_fields))
