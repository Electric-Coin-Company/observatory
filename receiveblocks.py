#!/usr/bin/python
# -*- coding: utf-8 -*-

from functools import wraps
from flask import Flask, abort, jsonify, request, Response, session
import config, json, os, sqlite3, sys

db_file = 'blocks.sqlite'
app = Flask(__name__)
app.config.from_object(config.FlaskConfig)

def createdb():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS tx( \
        hash TEXT(100) NOT NULL, \
        tx TEXT(100) NOT NULL, \
        FOREIGN KEY (hash) REFERENCES blocks(hash) \
        PRIMARY KEY(tx))')

    c.execute('CREATE TABLE IF NOT EXISTS blocks( \
        hash TEXT(100) NOT NULL, \
        confirmations REAL NOT NULL, \
        size REAL NOT NULL, \
        height REAL NOT NULL, \
        version REAL NOT NULL, \
        merkleroot TEXT(100) NOT NULL, \
        tx BLOB, \
        time REAL NOT NULL, \
        nonce TEXT(100) NOT NULL, \
        bits TEXT(50) NOT NULL, \
        difficulty TEXT(50) NOT NULL, \
        chainwork TEXT(100) NOT NULL, \
        anchor TEXT(100) NOT NULL, \
        previousblockhash TEXT(100), \
        nextblockhash TEXT(100), \
        arrivaltime REAL, \
        PRIMARY KEY (hash))')
    conn.execute('VACUUM')
    conn.commit()
    conn.close()

def storeblock(block):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO blocks (hash, confirmations, size, height, version, merkleroot, tx, \
            time, nonce, bits, difficulty, chainwork, anchor, previousblockhash, nextblockhash, arrivaltime) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (block['hash'], block['confirmations'], \
            block['size'], block['height'], block['version'], block['merkleroot'], json.dumps(block['tx']), block['time'], \
            block['nonce'], block['bits'], block['difficulty'], block['chainwork'], block['anchor'], \
            block.get('previousblockhash', None), block.get('nextblockhash', None), block.get('arrivaltime', None)))
        try:
            c.execute('UPDATE blocks SET nextblockhash = (?) WHERE hash = (?)', (block['hash'], block['previousblockhash']))
        except:
            pass
    except sqlite3.Error as err:
        print('ERROR:', err.message)
        if block['nextblockhash'] is not None:
            try:
                c.execute('UPDATE blocks SET nextblockhash=:nextblockhash WHERE hash=:hash',
                    {"nextblockhash": block['nextblockhash'], "hash": block['hash']})
                print 'Updated nextblockhash on block ' + block['height']
            except:
                pass
        try:
            c.execute('UPDATE blocks SET confirmations=:confirmations WHERE hash=:hash',
                {"confirmations": block['confirmations'], "hash": block['hash']})
            print 'Updated confirmations on block ' + block['height']
        except:
            pass
    for tx in block['tx']:
        try:
            c.execute('INSERT INTO tx (hash, tx) VALUES (?, ?)', (block['hash'], tx))
        except sqlite3.Error as err:
            print('ERROR:', err.message)
    conn.commit()
    conn.close()

@app.route('/', methods = ['POST'])
def index():
    print request.get_data()
    if request.method == 'POST' and request.content_type == 'application/json':
        storeblock(request.get_json())
        return ('', 204)

if __name__ == '__main__':
    createdb()
    app.run(host='0.0.0.0', port=int('8200'))
