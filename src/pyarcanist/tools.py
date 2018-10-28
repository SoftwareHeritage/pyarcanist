import os
from . import cli


ROWS, COLUMNS = map(int, os.popen('stty size', 'r').read().split())


def wrap(msg, width=COLUMNS):
    if len(msg) > width:
        return msg[:width-1] + '\u2026'
    return msg


def object_from_phid(phid):
    return cli.cnx.phid.query(phids=[phid])[phid]
