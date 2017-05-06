#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a Python Flask web application for displaying Zcash blocks.
"""
import ast
import re
import sqlite3
import time
from flask import Flask, render_template, request

import config
app = Flask(__name__)
app.config.from_object(config.ShowBlocksConfig)

def optimize_db(conn):
    c = conn.cursor()
    c.execute('PRAGMA journal_mode = WAL')
    c.execute('PRAGMA page_size = 8096')
    c.execute('PRAGMA temp_store = 2')
    c.execute('PRAGMA synchronous = 0')
    c.execute('PRAGMA cache_size = 8192000')
    conn.commit()
    return

def stats(count=False, txs=False, height=False, diff=False):
    conn = sqlite3.connect(app.config['DB_FILE'], timeout=30)
    optimize_db(conn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    summary = {}
    if count:
        c.execute('SELECT COUNT(*) FROM blocks')
        summary['count'] = c.fetchone()[0]
    if txs:
        c.execute('SELECT COUNT(*) FROM tx')
        summary['txs'] = c.fetchone()[0]
    if height:
        c.execute('SELECT MAX(height) FROM blocks')
        summary['height'] = c.fetchone()[0]
    if diff:
        c.execute('SELECT (MAX(height) - COUNT(*)) FROM blocks')
        summary['diff'] = c.fetchone()[0]
    conn.close()
    return stats

def find_block_by_tx(txid):
    conn = sqlite3.connect(app.config['DB_FILE'], timeout=30)
    optimize_db(conn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT hash FROM tx WHERE tx=:txid', {"txid": txid})
    block_hash = c.fetchone()
    conn.close()
    return str(block_hash['hash'])

def find_block_by_height(block_height):
    conn = sqlite3.connect(app.config['DB_FILE'], timeout=30)
    optimize_db(conn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT hash FROM blocks WHERE height=:height', {"height": block_height})
    block_hash = c.fetchone()
    conn.close()
    return str(block_hash['hash'])

def get_single_block(block_hash):
    conn = sqlite3.connect(app.config['DB_FILE'], timeout=30)
    optimize_db(conn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM blocks WHERE hash=:hash', {"hash": block_hash})
    block = c.fetchone()
    conn.close()
    transactions = ast.literal_eval(block['tx'])
    confirmations = (stats('count') - block['height']) + 1
    return dict(block), list(transactions), int(confirmations)

def get_blocks():
    conn = sqlite3.connect(app.config['DB_FILE'], timeout=30)
    optimize_db(conn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT hash, height, size, txs, time FROM blocks ORDER by height DESC LIMIT 200')
    # return retrieved blocks as a dict
    blocks = [dict(block) for block in c.fetchall()]
    conn.close()
    return blocks

def validate_input(search_string):
    if search_string.isdigit():
        if int(search_string) <= stats['height']:
            print('Search is numeric but not less than the current block height.')
            return search_string
    if len(search_string) != 64:
        print('Error: Search does not consist of 64 characters.')
        return None
    m = re.match(r"[A-Fa-f0-9]{64}", search_string)
    if m and m.span()[1] == len(search_string):
        print('Search matches hexademical format of a block hash or txid.')
        return search_string
    return None

@app.template_filter('timestamp')
def _jinja2_filter_timestamp(unix_epoch):
    return time.ctime(unix_epoch)

@app.route('/')
def index():
    try:
        blocks = get_blocks()
    except Exception as e:
        print('Error retreving blocks from the local database.')
        print(e)
        pass
    return render_template('blocks.html', blocks=blocks)

@app.route('/block', methods=['GET', 'POST'])
def show_block():
    print('Searching: ' + request.values.get('search'))
    search_string = validate_input(request.values.get('search').strip().lower())
    if search_string is None:
        print('Error: Search string was invalid.')
        return ('', 204)
    # find block by hash
    try:
        block, transactions, confirmations = get_single_block(search_string)
        return render_template('block.html', block=block, transactions=transactions, confirmations=confirmations)
    except Exception as e:
        print(e)
        print('Error: Failed to locate block by hash.')
        pass
    # find block by transaction ID
    try:
        block_hash = find_block_by_tx(search_string)
        block, transactions, confirmations = get_single_block(block_hash)
        return render_template('block.html', block=block, transactions=transactions, confirmations=confirmations)
    except Exception as e:
        print(e)
        print('Error: Failed to locate block by txid.')
        pass
    # find block by height
    try:
        block_hash = find_block_by_height(search_string)
        block, transactions, confirmations = get_single_block(block_hash)
        return render_template('block.html', block=block, transactions=transactions, confirmations=confirmations)
    except Exception as e:
        print(e)
        print('Error: Failed to locate block by height.')
        return ('', 204)

def main():
    census = stats(count=True, txs=False, height=True, diff=True)
    print (str(census['count']) + ' blocks available for search.')
    print (str(census['diff']) + ' blocks missing from the database.')
    app.run(host='0.0.0.0', port=int(app.config['BIND_PORT']), debug=app.config['DEBUG'])

if __name__ == '__main__':
    main()