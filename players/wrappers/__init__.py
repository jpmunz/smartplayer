from .. import settings

# TODO right now importing itunes on a non-windows machine fails a depedency for win32api
if settings.WRAPPER == 'ItunesWrapper':
    from itunes import ItunesWrapper
elif settings.WRAPPER == 'ExaileWrapper':
    from exaile import ExaileWrapper
else:
    raise Exception("Unrecognized wrapper '%s'" % settings.WRAPPER)
