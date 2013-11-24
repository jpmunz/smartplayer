import datetime
import os
from smartplayer import settings
from smartplayer.tracks import get_track_key, get_track_info, display_track
from smartplayer.utils import PersistedDict

MIN_DATE = datetime.datetime(1900, 1, 1).strftime(settings.DATE_FORMAT)

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

def report_by(path, field, friendly_name, aggregate_func=None, convert_func=None, default=None, order='desc', group_by=None, min_threshold=None, max_threshold=None, limit=None, prune=False, delete=False, exclude=False):

    # Sort the result
    def key_func(item):
        key = item.get(field, default)
        if convert_func:
            key = convert_func(key)

        return key

    tracks = get_track_info(path)

    # Deal with grouping
    if group_by:
        groups = {}

        for track_info in tracks:
            group_key = track_info.get(group_by)
            groups.setdefault(group_key, {})
            groups[group_key][field] = aggregate_func(key_func(groups[group_key]), key_func(track_info))
            groups[group_key][group_by] = group_key

        tracks = groups.values()

    result = sorted(tracks, key=key_func, reverse=(order == 'desc'))

    # Deal with thresholds
    if min_threshold or max_threshold:
        limited_result = []
        for item in result:
            if min_threshold and key_func(item) < convert_func(min_threshold):
                continue
            if max_threshold and key_func(item) > convert_func(max_threshold):
                continue

            limited_result.append(item)

        result = limited_result

    if limit:
        result = result[:limit]

    if prune or delete or exclude:
        if group_by:
            return

        db = PersistedDict(os.path.join(path, '.tracks'))
        for item in result:
            action = None
            if prune:
                prompt = "%s\nDelete this track? (y)es/(n)o/(e)xclude from shuffle\n" % display_track(item)
                prompt = prompt.encode("ascii", "ignore")

                while True:
                    ans = raw_input(prompt)
                    if ans in ['y', 'n', 'e']:
                        break
                if ans == 'y':
                    action = 'delete'
                elif ans == 'e':
                    action = 'exclude'
            elif exclude:
                action = 'exclude'
            elif delete:
                action = 'delete'

            if action == 'exclude':
                track_info = db[item['pk']]
                track_groups = track_info.get('groups', [])
                if 'exclude' not in track_groups:
                    track_groups.append('exclude')
                track_info['groups'] = track_groups
                db.save()
            elif action == 'delete':
                del db[item['pk']]
                db.save()
                os.remove(os.path.join(path, item['file_path']))
    else:
        # Just display
        for item in result:
            if group_by:
                display = item[group_by]
                if display is None:
                    display = "<Unknown>"
            else:
                display = display_track(item)

            value = item.get(field, default)

            if value == MIN_DATE:
                value = ""

            print "%s,\t%s: %s" % (display, friendly_name, value)

def report_by_rating(path, **kwargs):
    report_by_int(path, "rating", "Rating", **kwargs)

def report_by_listen_count(path, **kwargs):
    report_by_int(path, "listen_count", "Listen Count", **kwargs)

def report_by_skip_count(path, **kwargs):
    report_by_int(path, "skip_count", "Skip Count", **kwargs)

def report_by_date_added(path, **kwargs):
    report_by_date(path, "date_added", "Date Added", **kwargs)

def report_by_date_played(path, **kwargs):
    report_by_date(path, "date_played", "Date Played", **kwargs)

def report_by_int(path, field, friendly_field, **kwargs):
    report_by(path, field, friendly_field, default=0, aggregate_func=sum, convert_func=int, **kwargs)

def report_by_date(path, field, friendly_field, **kwargs):
    convert = lambda x: datetime.datetime.strptime(x, settings.DATE_FORMAT)
    report_by(path, field, friendly_field, default=MIN_DATE, aggregate_func=max, convert_func=convert, **kwargs)
