import sys
import gevent


greenlets = []


def die(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()
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


def shutdown():
    gevent.killall(greenlets)
