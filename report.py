import argparse
import settings
import requests
import json
from smartplayer import TrackDB

def report(tracks, list_accepted=False, list_undecided=False, list_disliked=False):

    result = []

    track_list = tracks.values()
    track_list = sorted(track_list, key=lambda t: -int(t['rating']))

    if list_accepted:
        accepted = lambda t: int(t['rating']) >= settings.ACCEPTED_RATING_THRESHOLD
        result.extend(get_tracks('Accepted Tracks', accepted, track_list))

    if list_undecided:
        undecided = lambda t: int(t['rating']) < settings.ACCEPTED_RATING_THRESHOLD and int(t['rating']) >= settings.DISLIKE_THRESHOLD
        result.extend(get_tracks('Undecided Tracks', undecided, track_list))

    if list_disliked:
        disliked = lambda t: int(t['rating']) < settings.DISLIKE_THRESHOLD
        result.extend(get_tracks('Disliked Tracks', disliked, track_list))

    if not (list_undecided or list_accepted or list_disliked):
        result.extend(get_tracks('Tracks', lambda t: True, track_list))

    return result


def get_tracks(header, filter_func, tracks):
    result = []

    filtered_tracks = filter(filter_func, tracks)
    result.append('')
    result.append('*****************************************')
    result.append('%s, Count: %d' % (header, len(filtered_tracks)))
    result.append('*****************************************')
    result.append('')
    result.extend([track_str(track) for track in filtered_tracks])

    return result


def track_str(track):
    return "%d %s by %s" % (track['rating'], track['name'], track['artist'])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Report on the tracks stored in the player DB')

    parser.add_argument('--list-accepted', action='store_true', default=False, help="List all accepted tracks")
    parser.add_argument('--list-undecided', action='store_true', default=False, help="List all undecided tracks")
    parser.add_argument('--list-disliked', action='store_true', default=False, help="List all disliked tracks")
    parser.add_argument('--upload-url', help="URL to post the report results to")

    args = parser.parse_args()

    result = report(TrackDB(settings.DB_FILE), list_accepted=args.list_accepted, list_undecided=args.list_undecided, list_disliked=args.list_disliked)

    if args.upload_url:
        requests.post(args.upload_url, data={'content': json.dumps(result)})

    print '\n'.join(result)
