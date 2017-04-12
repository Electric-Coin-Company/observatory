#!/usr/bin/python
# -*- coding: utf-8 -*-

from functools import wraps
from flask import Flask, g, abort, jsonify, render_template, request, Response, session
import config, json, os, re, sqlite3, sys, time
from werkzeug.contrib.cache import SimpleCache

db_file = 'blocks.sqlite'
app = Flask(__name__)
app.config.from_object(config.FlaskConfig)

def get_blocks(block_hash=None):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if block_hash is not None:
        c.execute('SELECT * FROM blocks WHERE hash=:hash', {"hash": block_hash})
        block = dict(c.fetchone())
        txs = get_txs(block['hash'])
        block['tx'] = txs
        return block
    else:
        c.execute('SELECT * FROM blocks ORDER by height DESC')
        blocks = [dict(block) for block in c.fetchall()]
        for block in blocks:
            txs = get_txs(block['hash'])
            block['tx'] = txs
        return blocks

def get_txs(block_hash):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT tx FROM tx WHERE hash=:hash', {"hash": block_hash})
    txs = [dict(tx) for tx in c.fetchall()]
    return txs

@app.template_filter('timestamp')
def _jinja2_filter_timestamp(unix_epoch):
    return time.ctime(unix_epoch)

@app.route('/')
def index():
    blocks = cache.get('blocks')
    return render_template('blocks.html', blocks = blocks)

@app.route('/block', methods = ['GET', 'POST'])
def show_block():
    try:
        block = get_blocks(request.values.get('search'))
        return render_template('block.html', block = block)
    except:
        return ('', 204)

if __name__ == '__main__':
    cache = SimpleCache()
    cache.set('blocks', get_blocks(), timeout=3600)
    app.run(host='0.0.0.0', port=int('8201'))
