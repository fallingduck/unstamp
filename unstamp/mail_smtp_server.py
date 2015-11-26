'''Unstamp Mail Transfer Agent Server

This server receives mail from the outside and sends it to the Mail Delivery
Agent (mail_delivery.py) for delivery.
'''


from gevent import socket
from gevent.server import StreamServer
from email.parser import FeedParser

from .error import error
from .util import writeline


_server = None
_hostname = ''


class _Envelope:
    def __init__(self):
        self.FROM = ''
        self.RECIPIENTS = []
        self.MESSAGE = None
        self._FEEDER = None
    def start_feed(self):
        self._FEEDER = FeedParser()
    def feed(self, lines):
        self._FEEDER.feed(lines)
        if lines.strip() == '.':
            return False
        return True
    def end_feed(self):
        self.MESSAGE = self._FEEDER.close()


def _parse_request(request):
    request = request.strip()


def _accept(fp, host, port):

    writeline(fp, '220 {0} ESMTP'.format(_hostname))
    verb, parameter = _parse_request(fp.readline())

    if verb == 'HELO':
        client_name = parameter
        envelope = _Envelope()
        writeline(fp, '250 OK')

    elif verb == 'EHLO':
        pass  # TODO

    else:
        writeline(fp, '500 Unrecognized Response')
        return



    while True:
        verb, parameter = _parse_request(fp.readline())

        if verb == 'MAIL':
            envelope.RECIPIENTS = []
            # TODO

        elif verb == 'RCPT':
            if not envelope.FROM:
                writeline(fp, '503 Need MAIL Before RCPT')
                continue
            # TODO

        elif verb == 'DATA':
            if not envelope.RECIPIENTS:
                writeline(fp, '503 Need RCPT Before Data')
                continue
            writeline(fp, '354 OK')
            envelope.start_feed()
            while envelope.feed(fp.readline()):
                pass
            envelope.end_feed()
            # TODO

        elif verb == 'QUIT':
            writeline(fp, '221 Farewell')
            break

        else:
            writeline(fp, '500 Unrecognized Response')


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
