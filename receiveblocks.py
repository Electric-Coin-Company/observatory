#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a Python Flask web application for storing Zcash blocks from elsewhere.
"""
import atexit
import json
import sqlite3
from flask import Flask, request
from config import ReceiveBlocksFlaskConfig, ReceiveBlocksConfig as config

app = Flask(__name__)
app.config.from_object(ReceiveBlocksFlaskConfig)

conn = sqlite3.connect(config.DB_FILE, **config.DB_ARGS)
conn.row_factory = sqlite3.Row


def createdb():
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


def closedb():
    conn.close()
    atexit.register(closedb)


def storeblock(block):
    c = conn.cursor()
    try:
        c.execute('INSERT INTO blocks (hash, confirmations, size, height, version, merkleroot, tx, txs, \
                  time, nonce, bits, difficulty, chainwork, anchor, previousblockhash, nextblockhash, arrivaltime) \
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (block['hash'], block['confirmations'], block['size'], block['height'], block['version'],
                   block['merkleroot'], json.dumps(block['tx']), len(block['tx']), block['time'], block['nonce'],
                   block['bits'], block['difficulty'], block['chainwork'], block['anchor'], block.get('previousblockhash', None),
                   block.get('nextblockhash', None), block.get('arrivaltime', None)))
        if block['nextblockhash'] is None:
            c.execute('UPDATE blocks SET nextblockhash = (?) WHERE hash = (?)', (block['hash'], block['previousblockhash']))
        else:
            c.execute('UPDATE blocks SET nextblockhash=:nextblockhash WHERE hash=:hash',
                      {"nextblockhash": block['nextblockhash'], "hash": block['hash']})
    except sqlite3.Error as err:
            print(err)
            pass
    for tx in block['tx']:
        try:
            c.execute('INSERT INTO tx (hash, tx) VALUES (?, ?)', (block['hash'], tx))
        except sqlite3.Error as err:
            print(err)
            pass
            continue
    conn.commit()
    return


@app.route('/', methods=['POST'])
def index():
    print(request.get_data())
    if request.method == 'POST' and request.content_type == 'application/json':
        storeblock(request.get_json())
        return('', 204)


def main():
    createdb()
    atexit.register(closedb)
    app.run(host='0.0.0.0', port=int(config.BIND_PORT))


if __name__ == '__main__':
    main()
