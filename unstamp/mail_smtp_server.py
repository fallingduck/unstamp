'''Unstamp Mail Transfer Agent Server

This server receives mail from the outside and sends it to the Mail Delivery
Agent (mail_delivery.py) for delivery.
'''


from gevent import socket
from gevent.server import StreamServer

from .error import error
from .util import writeline


_server = None
_hostname = ''


def _parse_request(request):
    request = request.strip()
    verb = request[:request.index(' ')]
    parameter = request[request.index(' ') + 1:].strip()
    return verb, parameter


def _accept(fp, host, port):
    writeline(fp, '220 {0} ESMTP'.format(_hostname))
    verb, parameter = _parse_request(fp.readline())
    if verb == 'HELO':
        client_name = parameter
        # TODO: initialize envelope
        writeline(fp, '250 OK')
    elif verb == 'EHLO':
        pass  # TODO
    else:
        return


def _handler(s, address):
    sf = s.makefile('r+', newline='')
    _accept(sf, *address)
    s.shutdown(socket.SHUT_RDWR)
    s.close()


def start(hostname, host, port):
    global _server, _hostname
    _hostname = hostname
    try:
        _server = StreamServer((host, port), _handler)
        _server.start()
    except PermissionError:
        raise error('Permission to access port {1} on {0} denied!'.format(host, port))


def stop():
    if _server is None:
        raise error('stop() called, but Mail Transfer Agent server is not running!')
    _server.stop()
