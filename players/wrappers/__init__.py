from .. import settings

if settings.WRAPPER == 'ItunesWrapper':
    from itunes import ItunesWrapper
elif settings.WRAPPER == 'ExaileWrapper':
    from exaile import ExaileWrapper
else:
    raise Exception("Unrecognized wrapper '%s'" % settings.WRAPPER)
