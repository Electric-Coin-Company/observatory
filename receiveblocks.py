#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a Python Flask web application for storing Zcash blocks from elsewhere.
"""
import json
import sqlite3
import subprocess
import sys
from flask import Flask, request

import config
app = Flask(__name__)
app.config.from_object(config.ReceiveBlocksConfig)

def createdb():
    conn = sqlite3.connect(app.config['DB_FILE'])
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS tx( \
        hash TEXT NOT NULL, \
        tx TEXT NOT NULL, \
        FOREIGN KEY (hash) REFERENCES blocks(hash) \
        PRIMARY KEY(tx))')

    c.execute('CREATE TABLE IF NOT EXISTS blocks( \
        hash TEXT NOT NULL, \
        confirmations INTEGER, \
        size INTEGER NOT NULL, \
        height INTEGER NOT NULL, \
        version REAL, \
        merkleroot TEXT(100) NOT NULL, \
        tx BLOB, \
        txs INTEGER, \
        time REAL NOT NULL, \
        nonce TEXT NOT NULL, \
        bits TEXT NOT NULL, \
        difficulty TEXT NOT NULL, \
        chainwork TEXT NOT NULL, \
        anchor TEXT NOT NULL, \
        previousblockhash TEXT, \
        nextblockhash TEXT, \
        arrivaltime REAL, \
        PRIMARY KEY (hash))')
    conn.execute('VACUUM')
    conn.commit()
    conn.close()

def find_gaps():
    conn = sqlite3.connect(app.config['DB_FILE'])
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
        return None
    else:
        for gap in gaps:
            print('Blocks between %d and %d are absent.' % (gap['start'], gap['end']))
        return gaps

def fill_gaps(gaps):
    commands = []
    procs = []
    exit_statuses = []
    for gap in gaps:
        commands.append(['/usr/bin/python', './loadblocks.py', '--start ' + str(gap['start']), '--end ' + str(gap['end'])])
    procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) for cmd in commands]
    for p in procs:
        print('Running %s as pid %d' % (p.args[1], p.pid))
    for p in procs:
        while p.poll() is None:
            sys.stdout.write(p.stdout.readline())
            sys.stdout.flush()
            p.kill()
    exit_statuses = [p.wait() for p in procs]
    print(exit_statuses)
    return True

def storeblock(block):
    conn = sqlite3.connect(app.config['DB_FILE'])
    c = conn.cursor()
    try:
        c.execute('INSERT INTO blocks (hash, confirmations, size, height, version, merkleroot, tx, txs, \
            time, nonce, bits, difficulty, chainwork, anchor, previousblockhash, nextblockhash, arrivaltime) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (block['hash'], block['confirmations'], \
            block['size'], block['height'], block['version'], block['merkleroot'], json.dumps(block['tx']), len(block['tx']), block['time'], \
            block['nonce'], block['bits'], block['difficulty'], block['chainwork'], block['anchor'], \
            block.get('previousblockhash', None), block.get('nextblockhash', None), block.get('arrivaltime', None)))
        try:
            c.execute('UPDATE blocks SET nextblockhash = (?) WHERE hash = (?)', (block['hash'], block['previousblockhash']))
        except:
            pass
    except sqlite3.Error as err:
        print('ERROR:', err)
        if block['nextblockhash'] is not None:
            try:
                c.execute('UPDATE blocks SET nextblockhash=:nextblockhash WHERE hash=:hash',
                          {"nextblockhash": block['nextblockhash'], "hash": block['hash']})
                print('Updated nextblockhash on block ' + block['height'])
            except:
                pass
        try:
            c.execute('UPDATE blocks SET confirmations=:confirmations WHERE hash=:hash',
                      {"confirmations": block['confirmations'], "hash": block['hash']})
            print('Updated confirmations on block ' + block['height'])
        except:
            pass
    for tx in block['tx']:
        try:
            c.execute('INSERT INTO tx (hash, tx) VALUES (?, ?)', (block['hash'], tx))
        except sqlite3.Error as err:
            print('ERROR:', err)
    conn.commit()
    conn.close()

@app.route('/', methods=['POST'])
def index():
    print(request.get_data())
    if request.method == 'POST' and request.content_type == 'application/json':
        storeblock(request.get_json())
        return ('', 204)

if __name__ == '__main__':
    createdb()
    fill_gaps(find_gaps())
    app.run(host='0.0.0.0', port=int(app.config['BIND_PORT']))
