import settings
import os
import json
import argparse
import eyed3
import kaa.metadata

class Id3DB(dict):
    def __init__(self, db_file):
        self.db_file = db_file

        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                db_data = f.read()

                if db_data:
                    self.update(json.loads(db_data))

            # Write a backup file in case something goes wrong
            with open(self.db_file + '~', 'w+') as f:
                f.write(json.dumps(self))

    def save(self):
        with open(self.db_file, 'w+') as f:
            f.write(json.dumps(self))

def generate_id3_db(path, db_file, reset):
    db = Id3DB(db_file)

    if reset:
        db.clear()

    music_files = []
    for root, dirs, files in os.walk(os.path.expanduser(path)):
        for file in files:
            if any(file.lower().endswith('.' + ext) for ext in ['wma', 'm4a', 'mp3', 'mp4']):
                music_files.append(root + '/' + file)

    fails = 0

    for file in music_files:
        escaped_file_name = json.loads(json.dumps(file))

        try:
            if not json.loads(json.dumps(file)) in db:
                id3_info = eyed3.load(file)
                db[file] = {
                    'artist': id3_info.tag.artist,
                    'title': id3_info.tag.title,
                    'comments': ','.join(comment.text for comment in id3_info.tag.comments),
                    'duration': id3_info.info.time_secs,
                }
        except Exception, e:
            try:
                info = kaa.metadata.parse(file)
                db[file] = {
                    'artist': info.artist,
                    'title': info.title,
                    'comments': '',
                    'duration': int(info.length),
                }
            except Exception, e:
                print "Failed to load information for %s, error:%s" % (file, e.message)
                fails += 1


        if escaped_file_name in db and file in db and escaped_file_name != file:
            print "Both escaped and unescaped in db for %s" % file
            fails += 1

        if escaped_file_name in db:
            track = db[escaped_file_name]
        elif file in db:
            track = db[file]

        if (track['comments'] != 'exclude') and (not track['artist'] or not track['title'] or not track['duration']):
            print "Missing id3 tags for %s" % file
            fails += 1



    db.save()

    if fails:
        print "fail count: %d" % fails

    return db

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stores id3 tag information for all mp3s in the given path')
    parser.add_argument('path')
    parser.add_argument('--reset-db', action='store_true', default=False, help="Resets entries in the DB")
    parser.add_argument('--db-file', type=str, default='.id3_db', help="File to store the id3 results to")
    args = parser.parse_args()

    generate_id3_db(args.path, args.db_file, args.reset_db)