#! /usr/bin/env python3

__author__  = 'Jacob (Jack) VanDrunen'
__version__ = 'pre-alpha'
__license__ = 'ISC'


from .error import error
from .util import die
from . import mtaserver

try:
    from .config import config
except error as e:
    die(e)


if config['MTA_ENABLED']:
    print('Starting MTA server...')
    try:
        mtaserver.start(config['HOSTNAME'], config['MTA_HOST'], config['MTA_PORT'])
        print('Done.')
    except KeyError as e:
        die('Missing value in config file: {0}'.format(e))
    except error as e:
        die(e)
