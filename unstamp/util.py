import sys


def die(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()
    sys.exit(1)
