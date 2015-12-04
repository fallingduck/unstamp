'''Unstamp Mail Transfer Agent Server

This server receives mail from the outside and sends it to the Mail Delivery
Agent (mail_delivery.py) for delivery.
'''


from gevent import socket
from gevent.server import StreamServer

from .error import error
from .util import log, printerr, writeline, readline, spawn, add_greenlet
from .database import Address
from .mail_delivery import deliver


_hostname = ''
_maxsize = 0


class _Envelope:
    def __init__(self):
        self.reset()
    def reset(self):
        self._from = ''
        self._recipients = set()
        self._message = ''
    def mailfrom(self, addr):
        self._from = addr
    def received_from(self):
        return bool(self._from)
    def rcptto(self, addr):
        self._recipients.append(addr)
    def rcpt_len(self):
        return len(self._recipients)
    def start_feed(self):
        self._message = ''
    def feed(self, line):
        self._message += line
        if self._message[-5:] == '\r\n.\r\n':
            return False
        return True
    def valid(self, maxsize):
        if not maxsize:
            return True
        return len(self._message) <= maxsize


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


def _accept(s, host, port):

    writeline(s, '220 {0} ESMTP'.format(_hostname))
    verb, parameter = _parse_request(readline(s))

    envelope = _Envelope()
    helo_received = False

    if verb == 'HELO':
        client_name = parameter
        writeline(s, '250 OK')
        helo_received = True

    elif verb == 'EHLO':
        client_name = parameter
        writeline(s, '250-{0}'.format(_hostname))
        writeline(s, '250-8BITMIME')
        if _maxsize:
            writeline(s, '250-SIZE {0}'.format(_maxsize))
        writeline(s, '250 PIPELINING')
        helo_received = True

    else:
        client_name = ''

    if client_name:
        log('MTA: {0} identifies as {1}'.format(host, client_name))
    else:
        log('MTA: {0} did not identify!'.format(host))



    while True:
        if helo_received:
            verb, parameter = _parse_request(readline(s))
        else:
            helo_received = True

        if verb == 'MAIL':
            parameter = parameter.lower()
            if parameter[:5] != 'from:':
                writeline(s, '500 No Address Given')
                continue
            mailfrom = parse_address(parameter[5:])
            if not mailfrom:
                writeline(s, '501 Malformatted Address')
                continue
            if _maxsize:
                try:
                    size = int(parameter.split(' size=')[-1].split(' ')[0])
                    if size > _maxsize:
                        writeline(s, '552 Too Big')
                        continue
                except Exception:
                    pass
            envelope.reset()
            envelope.mailfrom(mailfrom)
            writeline(s, '250 OK')

        elif verb == 'RCPT':
            if not envelope.received_from():
                writeline(s, '503 Need MAIL Before RCPT')
                continue
            if envelope.rcpt_len() >= 100:
                writeline(s, '452 Too Many Recipients')
                continue
            parameter = parameter.lower()
            if parameter[:3] != 'to:':
                writeline(s, '500 No Address Given')
                continue
            rcptto = parse_address(parameter[3:])
            if rcptto is None:
                writeline(s, '501 Malformatted Address')
                continue
            account = Address.select().where(Address.email == rcptto)
            if not account.exists():
                writeline(s, '550 Not A Valid Address')
                continue
            envelope.rcptto(rcptto)
            writeline(s, '250 OK')

        elif verb == 'DATA':
            if not envelope.rcpt_len():
                writeline(s, '503 Need RCPT Before Data')
                continue
            envelope.start_feed()
            writeline(s, '354 OK')
            while envelope.feed(readline(s)):
                pass
            if not envelope.valid(_maxsize):
                writeline(s, '552 Too Big')
                envelope = _Envelope()
                continue
            mailman = spawn(deliver, envelope)
            writeline(s, mailman.get())
            envelope = _Envelope()

        elif verb == 'RSET':
            envelope = _Envelope()
            writeline(s, '250 OK')

        elif verb == 'NOOP':
            writeline(s, '250 OK')

        elif verb == 'QUIT':
            writeline(s, '221 Farewell')
            break

        elif verb == 'VRFY':
            if parameter:
                writeline(s, '252 Try Me')
            else:
                writeline(s, '500 No VRFY Parameter')

        else:
            writeline(s, '500 Unrecognized Response')


def _handler(s, address):
    add_greenlet()
    log('MTA: Got connection from {0}'.format(address[0]))
    try:
        _accept(s, *address)
    except BaseException as e:
        printerr('MTA: {0}'.format(e))
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        log('MTA: Connection from {0} closed'.format(address[0]))


def set_hostname(hostname):
    global _hostname
    _hostname = hostname


def set_maxsize(size):
    global _maxsize
    _maxsize = size


def start(host, port):
    try:
        server = StreamServer((host, port), _handler)
        server.start()
        return server
    except PermissionError:
        raise error('Permission to access port {1} on {0} denied!'.format(host, port))
