import json

from .error import error


def _split(line):
    key = line.split()[0]
    value = line[len(key):].strip()
    value = json.loads(value)
    return key, value


try:
    config = {}
    with open('./config.dat', 'r') as f:
        for line in f:
            line = line.strip()
            if line and line[0] != '#':
                key, value = _split(line)
                config[key] = value
except Exception:
    raise error('Error reading config file')
