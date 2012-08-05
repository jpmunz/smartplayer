import argparse
import settings
from smartplayer import TrackDB


def report(tracks, list_accepted=False, list_undecided=False):

    result = []

    track_list = tracks.values()
    track_list = sorted(track_list, key=lambda t: -int(t['rating']))

    if list_accepted:
        accepted = lambda t: int(t['rating']) >= settings.ACCEPTED_RATING_THRESHOLD
        result.extend(get_tracks('Accepted Tracks', accepted, track_list))

    if list_undecided:
        undecided = lambda t: int(t['rating']) < settings.ACCEPTED_RATING_THRESHOLD
        result.extend(get_tracks('Undecided Tracks', undecided, track_list))

    if not (list_undecided or list_accepted):
        result.extend(get_tracks('Tracks', lambda t: True, track_list))

    return result


def get_tracks(header, filter_func, tracks):
    result = []

    filtered_tracks = filter(filter_func, tracks)
    result.append('%s %d' % (header, len(filtered_tracks)))
    result.extend([track_str(track) for track in filtered_tracks])

    return result


def track_str(track):
    return "%d %s by %s" % (track['rating'], track['name'], track['artist'])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Report on the tracks stored in the player DB')

    parser.add_argument('--list-accepted', action='store_true', default=False, help="List all accepted tracks")
    parser.add_argument('--list-undecided', action='store_true', default=False, help="List all undecided tracks")

    args = parser.parse_args()

    result = report(TrackDB(settings.DB_FILE), list_accepted=args.list_accepted, list_undecided=args.list_undecided)

    print '\n'.join(result)
