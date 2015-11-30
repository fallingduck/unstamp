#! /usr/bin/env python3

__author__  = 'Jacob (Jack) VanDrunen'
__version__ = 'pre-alpha'
__license__ = 'ISC'


from gevent import monkey
monkey.patch_all()

from .error import error
from .util import die
from . import mail_smtp_server as smtp_server

try:
    from .config import config
except error as e:
    die(e)


if 'MTA_BIND' in config:
    print('Starting MTA server(s)...')
    try:
        for mta_host, mta_port in config['MTA_BIND']:
            smtp_server.start(config['HOSTNAME'], mta_host, mta_port)
            print('MTA server started on port {1} on {0}'.format(mta_host, mta_port))
    except ValueError as e:
        die('Bad value in config file: MTA_BIND')
    except KeyError as e:
        die('Missing value in config file: {0}'.format(e))
    except error as e:
        die(e)
