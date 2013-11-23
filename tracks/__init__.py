import settings
import os
import json
import argparse
from utils import PersistedDict
import eyed3
import kaa.metadata

SUPPORTED_FILE_TYPES = ['wma', 'm4a', 'mp3', 'mp4']

class ID3Exception(Exception): pass
class LoadException(Exception): pass

def find_files(path, types=SUPPORTED_FILE_TYPES):
    found = []
    for root, dirs, files in os.walk(os.path.expanduser(path)):
        for f in files:
            if any(f.lower().endswith('.' + ext) for ext in types):
                found.append(root + '/' + f)

    return found

def load_id3_information(file_path):
    failures = []

    for method in (_attempt_eyed3_load, _attempt_kaa_load):
        data = method(file_path)
        if data:
            break

    if data:
        return data
    else:
        raise ID3Exception("Failed to load information for %s" % file_path)

def _attempt_eyed3_load(file_path):
    try:
        id3_info = eyed3.load(file_path)
        return {
            'artist': id3_info.tag.artist,
            'album': id3_info.tag.album,
            'title': id3_info.tag.title,
            'duration': id3_info.info.time_secs,
        }
    except Exception, e:
        pass

def _attempt_kaa_load(file_path):
    try:
        id3_info = kaa.metadata.parse(file_path)

        return {
            'artist': id3_info.artist,
            'title': id3_info.title,
            'duration': int(id3_info.length),
        }
    except Exception, e:
        pass

def get_track_key(json_data):
    if not (json_data.get('artist') and json_data.get('title')):
        return None
    else:
        return '$'.join(json_data.get(k) or '' for k in ('artist', 'title', 'album'))

def display_track(json_data):
    if 'artist' in json_data and 'title' in json_data:
        return "%s By %s" % (json_data['title'], json_data['artist'])
    else:
        return "%s" % json_data['file_path']

def update_from_path(path, overwrite=False, verbose=False):
    db = PersistedDict(os.path.join(path, '.tracks'), overwrite=overwrite)
    not_seen = set(db.keys())
    track_info_added = {}
    failures = []
    for file_path in find_files(path):
        escaped_file_path = json.loads(json.dumps(file_path))

        if escaped_file_path in db:
            not_seen.remove(escaped_file_path)
        else:
            if verbose:
                print "Attempting to add new file: '%s':" % escaped_file_path

            try:
                id3_info = load_id3_information(file_path)
            except ID3Exception, e:
                raise e
                failures.append(e)

            track_info = {
                'file_path': escaped_file_path,
                'pk': escaped_file_path
            }
            track_info.update(id3_info)

            db[escaped_file_path] = track_info
            track_key = get_track_key(track_info)

            if track_key:
                if track_key in track_info_added:
                    failures.append(LoadException("Added multiple files with the same ID3 information: '%s' and '%s'" % (escaped_file_path, track_info_added[track_key]['file_path'])))


                track_info_added[get_track_key(track_info)] = track_info

    claimed_renames = {}
    # Remove missing entries
    for file_path in not_seen:
        # Check for rename
        track_key = get_track_key(db[file_path])
        if track_key and track_key in track_info_added:
            new_name = track_info_added[track_key]['file_path']
            if track_key in claimed_renames:
                failures.append(LoadException("Cannot resolve rename, two previously tracked files are no longer found: '%s' and '%s', there is a new file with the same id3 information: '%s'" % (file_path, claimed_renames[track_key], new_name)))
            # Grab any information we may have had under the old named
            db[new_name] = dict(db[file_path].items() + db[new_name].items())
            claimed_renames[track_key] = file_path
            if verbose:
                print "Renamed '%s' to '%s'" % (file_path, new_name)

        else:
            if verbose:
                print "Removing missing file: '%s':" % file_path

        del db[file_path]

    db.save()

    for fail in failures:
        print fail
