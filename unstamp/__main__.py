#! /usr/bin/env python3

__author__  = 'Jacob (Jack) VanDrunen'
__version__ = 'pre-alpha'
__license__ = 'ISC'


from gevent import monkey, wait
monkey.patch_all()

from .error import error
from .util import set_logging, die, spawn, shutdown, greenlet_cleaner
from . import mail_smtp_server as smtp_server

try:
    from .config import config
except error as e:
    die(e)


servers = []


if 'LOGGING' in config:
    set_logging(config['LOGGING'])

if 'MTA_BIND' in config:
    print('Starting MTA server(s)...')
    try:
        for mta_host, mta_port in config['MTA_BIND']:
            smtp_server.set_hostname(config['HOSTNAME'])
            smtp_server.set_maxsize(config['MTA_MAX_SIZE'])
            servers.append(smtp_server.start(mta_host, mta_port))
            print('MTA server started on port {1} of {0}'.format(mta_host, mta_port))
    except ValueError as e:
        die('Bad value in config file: MTA_BIND')
    except KeyError as e:
        die('Missing value in config file: {0}'.format(e))
    except error as e:
        die(e)

spawn(greenlet_cleaner)


try:
    wait()
except (KeyboardInterrupt, SystemExit):
    for server in servers:
        try:
            server.stop()
            print('Stopped server on port {1} of {0}'.format(server.server_host, server.server_port))
        except Exception:
            continue
    shutdown()
    print('Goodbye!')
