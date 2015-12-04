import sys
import io
import gevent


_logging = False
_greenlets = []


def set_logging(value):
    global _logging
    _logging = value


def log(message):
    if _logging:
        print(message)


def printerr(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()


def die(message):
    printerr(message)
    print('Quitting...')
    sys.exit(1)


def writeline(s, line):
    s.sendall(bytes('{0}\r\n'.format(line), 'utf-8'))


def readline(s):
    line = io.BytesIO()
    gotcr = False
    while True:
        c = s.recv(1)
        line.write(c)
        if c == '\r':
            gotcr = True
        elif c == '\n' and gotcr:
            break
        elif gotcr:
            gotcr = False
    line.seek(0)
    return line.read()


def readmessage(s):
    message = io.BytesIO()
    lastfive = ''
    while True:
        c = s.recv(1)
        message.write(c)
        if c == '\r':
            if not lastfive:
                lastfive = '\r'
                continue
            elif lastfive == '\r\n.':
                lastfive = '\r\n.\r'
                continue
        elif c == '\n':
            if lastfive == '\r':
                lastfive = '\r\n'
                continue
            elif lastfive == '\r\n.\r':
                break
        elif c == '.':
            if lastfive == '\r\n':
                lastfive == '\r\n.'
                continue
        if lastfive:
            lastfive = ''
    message.seek(0)
    return message.read()


def spawn(*args, **kwargs):
    greenlet = gevent.spawn(*args, **kwargs)
    _greenlets.append(greenlet)
    return greenlet


def add_greenlet():
    _greenlets.append(gevent.getcurrent())


def shutdown():
    gevent.killall(_greenlets)


def greenlet_cleaner():
    current = gevent.getcurrent()
    while True:
        gevent.sleep(1000)
        gevent.idle()
        if current not in _greenlets:
            _greenlets.append(current)
        todelete = []
        for i, greenlet in enumerate(_greenlets):
            if greenlet.ready():
                todelete.append(i)
        for i in todelete:
            del _greenlets[i]
