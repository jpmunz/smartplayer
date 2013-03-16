from smartplayer import settings

if settings.WRAPPER == 'ItunesWrapper':
    from itunes.ituneswrapper import ItunesWrapper
elif settings.WRAPPER == 'ExaileWrapper':
    from exaile.exailewrapper import ExaileWrapper
else:
    raise Exception("Unrecognized wrapper '%s'" % settings.WRAPPER)
