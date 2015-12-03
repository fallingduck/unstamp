'''Unstamp Mail Transfer Agent Server

This server receives mail from the outside and sends it to the Mail Delivery
Agent (mail_delivery.py) for delivery.
'''


from gevent import socket
from gevent.server import StreamServer
from email.parser import FeedParser

from .error import error
from .util import printerr, writeline, spawn, add_greenlet
from .database import Address
from .mail_delivery import deliver


_hostname = ''


class _Envelope:
    def __init__(self):
        self.FROM = ''
        self.RECIPIENTS = set()
        self.MESSAGE = None
        self._FEEDER = None
    def start_feed(self):
        self._FEEDER = FeedParser()
    def feed(self, line):
        self._FEEDER.feed(line)
        if line == '.\r\n':
            return False
        return True
    def end_feed(self):
        self.MESSAGE = self._FEEDER.close()


def _parse_request(request):
    request = request.strip()
    if ' ' in request:
        space = request.index(' ')
        verb = request[:space]
        parameter = request[space:].lstrip()
    else:
        verb = request
        parameter = ''
    return verb, parameter


def parse_address(encoded):
    address = []
    encoded = encoded.strip()
    if not encoded or encoded[0] != '<':
        return
    inside_quotes = False
    i = 1
    if encoded[i] == '@':
        while encoded[i] != ':':
            i += 1
        i += 1
    while True:
        if i >= len(encoded):
            return  # Address is not properly terminated with '>'
        char = encoded[i]
        if char == '\\':
            i += 1
            address.append(encoded[i])
        elif char == '"':
            inside_quotes = not inside_quotes
        elif char == '>' and not inside_quotes:
            return ''.join(address)
        else:
            address.append(char)
        i += 1


def _accept(fp, host, port):

    writeline(fp, '220 {0} ESMTP'.format(_hostname))
    verb, parameter = _parse_request(fp.readline())

    envelope = _Envelope()
    helo_received = False

    if verb == 'HELO':
        client_name = parameter
        writeline(fp, '250 OK')
        helo_received = True

    elif verb == 'EHLO':
        client_name = parameter
        writeline(fp, '250-{0}'.format(_hostname))
        writeline(fp, '250-8BITMIME')
        writeline(fp, '250 PIPELINING')
        helo_received = True

    else:
        client_name = ''



    while True:
        if helo_received:
            verb, parameter = _parse_request(fp.readline())
        else:
            helo_received = True

        if verb == 'MAIL':
            parameter = parameter.lower()
            if parameter[:5] != 'from:':
                writeline(fp, '500 No Address Given')
                continue
            mailfrom = parse_address(parameter[5:])
            if not mailfrom:
                writeline(fp, '501 Malformatted Address')
                continue
            envelope.FROM = mailfrom
            envelope.RECIPIENTS = set()
            writeline(fp, '250 OK')

        elif verb == 'RCPT':
            if not envelope.FROM:
                writeline(fp, '503 Need MAIL Before RCPT')
                continue
            if len(envelope.RECIPIENTS) >= 100:
                writeline(fp, '452 Too Many Recipients')
                continue
            parameter = parameter.lower()
            if parameter[:3] != 'to:':
                writeline(fp, '500 No Address Given')
                continue
            rcptto = parse_address(parameter[3:])
            if rcptto is None:
                writeline(fp, '501 Malformatted Address')
                continue
            account = Address.select().where(Address.email == rcptto)
            if not account.exists():
                writeline(fp, '550 Not A Valid Address')
                continue
            envelope.RECIPIENTS.add(rcptto)
            writeline(fp, '250 OK')

        elif verb == 'DATA':
            if not envelope.RECIPIENTS:
                writeline(fp, '503 Need RCPT Before Data')
                continue
            envelope.start_feed()
            writeline(fp, '354 OK')
            while envelope.feed(fp.readline()):
                pass
            envelope.end_feed()
            mailman = spawn(deliver, envelope)
            writeline(fp, mailman.get())
            envelope = _Envelope()

        elif verb == 'RSET':
            envelope = _Envelope()
            writeline(fp, '250 OK')

        elif verb == 'NOOP':
            writeline(fp, '250 OK')

        elif verb == 'QUIT':
            writeline(fp, '221 Farewell')
            break

        elif verb == 'VRFY':
            if parameter:
                writeline(fp, '252 Try Me')
            else:
                writeline(fp, '500 No VRFY Parameter')

        else:
            writeline(fp, '500 Unrecognized Response')


def _handler(s, address):
    add_greenlet()
    sf = s.makefile('r+', newline='')
    try:
        _accept(sf, *address)
    except BaseException as e:
        printerr('MTA Server Handler: {0}'.format(e))
    finally:
        sf.close()
        s.shutdown(socket.SHUT_RDWR)
        s.close()


def set_hostname(hostname):
    global _hostname
    _hostname = hostname


def start(host, port):
    try:
        server = StreamServer((host, port), _handler)
        server.start()
        return server
    except PermissionError:
        raise error('Permission to access port {1} on {0} denied!'.format(host, port))
