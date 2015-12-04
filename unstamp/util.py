import sys
import io
import gevent


greenlets = []


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
        line.write(s.recv(1))
        if c == '\r':
            gotcr = True
        elif c == '\n' and gotcr:
            break
        elif gotcr:
            gotcr = False
    line.seek(0)
    return line.read()


def spawn(*args, **kwargs):
    greenlet = gevent.spawn(*args, **kwargs)
    greenlets.append(greenlet)
    return greenlet


def add_greenlet():
    greenlets.append(gevent.getcurrent())


def shutdown():
    gevent.killall(greenlets)


def greenlet_cleaner():
    current = gevent.getcurrent()
    while True:
        gevent.sleep(1000)
        gevent.idle()
        if current not in greenlets:
            greenlets.append(current)
        todelete = []
        for i, greenlet in enumerate(greenlets):
            if greenlet.ready():
                todelete.append(i)
        for i in todelete:
            del greenlets[i]
