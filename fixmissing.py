#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a Python Flask web application for storing Zcash blocks from elsewhere.
"""
import sqlite3
import subprocess
import sys
from config import ReceiveBlocksConfig as config


def find_gaps():
    conn = sqlite3.connect(config.DB_FILE, **config.DB_ARGS)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT (t1.height + 1) AS start, \
        (SELECT MIN(t3.height) -1 FROM blocks t3 WHERE t3.height > t1.height) AS end \
        FROM blocks t1 \
        WHERE NOT EXISTS (SELECT t2.height FROM blocks t2 WHERE t2.height = t1.height + 1) \
        GROUP BY height HAVING end IS NOT NULL \
        ORDER BY end DESC')
    gaps = [dict(gap) for gap in c.fetchall()]
    if gaps == []:
        sys.exit(0)
    else:
        for gap in gaps:
            print('Blocks between %d and %d are absent.' % (gap['start'], gap['end']))
        return gaps


def fill_gaps(gaps):
    commands = []
    procs = []
    for gap in gaps:
        commands.append(['/usr/bin/python', './loadblocks.py', '--start ' + str(gap['start']), '--end ' + str(gap['end'])])
    procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) for cmd in commands]
    for p in procs:
        print('Running %s as pid %d' % (p.args[1], p.pid))
    for p in procs:
        while p.poll() is None:
            sys.stdout.write(p.stdout.readline())
            sys.stdout.flush()
    return [p.wait() for p in procs]


def main():
    fill_gaps(find_gaps())
    sys.exit(0)


if __name__ == '__main__':
    main()
