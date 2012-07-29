import argparse
import settings
from smartplayer import TrackDB, DB_FILE


def report(tracks, list_accepted=False, list_undecided=False):

    result = []

    track_list = tracks.values()
    track_list = sorted(track_list, key=lambda t: -int(t['rating']))

    if list_accepted:
        accepted_tracks = filter(lambda t: int(t['rating']) >= settings.ACCEPTED_RATING_THRESHOLD)
        result.append('Accepted Tracks %d' % (len(accepted_tracks)))
        result.extend([track_str(track) for track in accepted_tracks])
    elif list_undecided:
        undecided_tracks = filter(lambda t: int(t['rating']) < settings.ACCEPTED_RATING_THRESHOLD)
        result.append('Undecided Tracks %d' % (len(undecided_tracks)))
        result.extend([track_str(track) for track in undecided_tracks])
    else:
        result.append('Tracks %d' % (len(track_list)))
        result.extend([track_str(track) for track in track_list])

    return result


def track_str(track):
    return "%d %s by %s" % (track['rating'], track['name'], track['artist'])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Report on the tracks stored in the player DB')

    parser.add_argument('--list-accepted', action='store_true', default=False, help="List all accepted tracks")
    parser.add_argument('--list-undecided', action='store_true', default=False, help="List all undecided tracks")

    args = parser.parse_args()

    result = report(TrackDB(DB_FILE), list_accepted=args.list_accepted, list_undecided=args.list_undecided)

    print '\n'.join(result)
