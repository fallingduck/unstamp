import sys
import gevent


greenlets = []


def printerr(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()


def die(message):
    printerr(message)
    print('Quitting...')
    sys.exit(1)


def writeline(fp, line):
    fp.write(line)
    fp.write('\r\n')
    fp.flush()


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
