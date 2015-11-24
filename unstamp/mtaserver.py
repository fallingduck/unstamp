from gevent import socket
from gevent.server import StreamServer

from .error import error


_server = None


def _handler(s, address):
    host, port = address
    # TODO
    s.shutdown(socket.SHUT_RDWR)
    s.close()


def start(host, port):
    global _server
    try:
        _server = StreamServer((host, port), _handler)
        _server.start()
    except PermissionError:
        raise error('Permission to access {0}:{1} denied!'.format(host, port))


def stop():
    if _server is None:
        raise error('stop() called, but Mail Transfer Agent server is not running!')
    _server.stop()
