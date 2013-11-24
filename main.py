#!/home/jon/code/smartplayer/env/bin/python
import argparse
from smartplayer.tracks import update_from_path
from smartplayer import reporting
from smartplayer import settings
from smartplayer import players

REPORT_BY_TYPES = ['rating', 'listen_count', 'skip_count', 'date_added', 'date_played']

def init_db(args):
    update_from_path(args.directory, verbose=args.verbose, overwrite=args.overwrite, types=args.types.split(','))

def report_duplicates(args):
    reporting.report_duplicates(args.directory)

def report_missing(args):
    reporting.report_missing(args.directory, tags=args.tags.split(','))

def report_by(args):
    report_by_func = getattr(reporting, 'report_by_%s' % args.by)

    if not report_by_func:
        print "Invalid report_by option: %s" % args.by
        return

    if args.group_by and (args.prune or args.delete or args.exclude):
        print "Cannot prune items when using group by"
        return

    report_by_func(args.directory, order=args.order, min_threshold=args.min_threshold, max_threshold=args.max_threshold, group_by=args.group_by, limit=args.limit, prune=args.prune, delete=args.delete, exclude=args.exclude)

def play(args):
    players.play(args.directory, player=args.player, accepted_threshold=args.accepted_threshold, undecided_play_rate=args.undecided_rate, verbose=args.verbose)

def main():
    parser = argparse.ArgumentParser(description="Manages and plays your music library")
    subparsers = parser.add_subparsers()

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('-v', '--verbose', action='store_true')
    common_parser.add_argument('-d', '--directory', default='.')

    play_parser = subparsers.add_parser('play', help="Plays tracks in the current directory tree", parents=[common_parser])
    play_parser.set_defaults(func=play)
    play_parser.add_argument('-p', '--player', default=settings.WRAPPER)
    play_parser.add_argument('-a', '--accepted-threshold', help="Rating threshold to consider a track accepted", default=settings.ACCEPTED_THRESHOLD)
    play_parser.add_argument('-u', '--undecided-rate', help="Percent of time to play undecided tracks", default=settings.UNDECIDED_PLAY_RATE)

    init_parser = subparsers.add_parser('init', help="Initialize a new .tracks database in the current directory", parents=[common_parser])
    init_parser.set_defaults(func=init_db)
    init_parser.add_argument('-o', '--overwrite', help='Replace existing .tracks file', action='store_true')
    init_parser.add_argument('-t', '--types', help='File types to look at', default=','.join(settings.FILE_TYPES_TO_LOAD))

    report_parser = subparsers.add_parser('report', help="Report on the .tracks in the current directory tree", parents=[common_parser])
    report_sub_parsers = report_parser.add_subparsers()

    report_duplicates_parser = report_sub_parsers.add_parser('duplicates')
    report_duplicates_parser.set_defaults(func=report_duplicates)

    report_missing_parser = report_sub_parsers.add_parser('missing')
    report_missing_parser.set_defaults(func=report_missing)
    report_missing_parser.add_argument('-t', '--tags', help="Which tags to care about", default=','.join(settings.ID3_TAGS_TO_REPORT_MISSING))

    report_by_parser = argparse.ArgumentParser(add_help=False)
    report_by_parser.add_argument('--order', help="asc or desc", default="desc")
    report_by_parser.add_argument('--min-threshold', help="Report entries above this value")
    report_by_parser.add_argument('--max-threshold', help="Report entries below this value")
    report_by_parser.add_argument('--limit', type=int, help="Report a maximum number of entries")
    report_by_parser.add_argument('--group-by', help="Group entry results by the given field (artist, album, etc.)")
    report_by_parser.add_argument('--prune', action="store_true", help="For each result prompt to remove or exclude")
    report_by_parser.add_argument('--exclude', action="store_true", help="Exclude each result from shuffle")
    report_by_parser.add_argument('--delete', action="store_true", help="Delete each result, USE WITH CAUTION")

    # Add a parser for each thing we want to report by
    for name in REPORT_BY_TYPES:
        report_by_sub_parser = report_sub_parsers.add_parser(name, parents=[report_by_parser])
        report_by_sub_parser.set_defaults(func=report_by, by=name)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
