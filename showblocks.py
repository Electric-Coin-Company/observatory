#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a Python Flask web application for displaying Zcash blocks.
"""
import ast
import atexit
import re
import sqlite3
import time
import sys
from flask import Flask, render_template, request, make_response
from werkzeug.contrib.cache import SimpleCache
from config import ShowBlocksFlaskConfig, ShowBlocksConfig as config
from helpers import blockcount, get_raw_tx
from receiveblocks import closedb

app = Flask(__name__)
app.config.from_object(ShowBlocksFlaskConfig)
cache = SimpleCache()

conn = sqlite3.connect(config.DB_FILE, **config.DB_ARGS)
conn.row_factory = sqlite3.Row

def stats(count=False, txs=False, height=False, diff=False):
    try:
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
    except Exception as err:
        print(err)
        sys.exit(1)
    return summary


def find_block_by_tx(txid):
    c = conn.cursor()
    c.execute('SELECT hash FROM tx WHERE tx=:txid', {"txid": txid})
    block_hash = c.fetchone()
    return str(block_hash['hash'])


def find_block_by_height(block_height):
    c = conn.cursor()
    c.execute('SELECT hash FROM blocks WHERE height=:height', {"height": block_height})
    block_hash = c.fetchone()
    return str(block_hash['hash'])


def get_single_block(block_hash):
    c = conn.cursor()
    c.execute('SELECT * FROM blocks WHERE hash=:hash', {"hash": block_hash})
    block = c.fetchone()
    transactions = ast.literal_eval(block['tx'])
    confirmations = blockcount() - block['height'] + 1
    return dict(block), list(transactions), int(confirmations)


def get_blocks(num_blocks=-1):
    c = conn.cursor()
    c.execute('SELECT hash, height, size, txs, time FROM blocks ORDER by height DESC LIMIT ' + (str(num_blocks) if (int(num_blocks) > 0) else str('-1')))
    blocks = [dict(block) for block in c.fetchall()]
    return blocks


def cached_blocks():
    if cache.get('blocks') is None:
        cache.set('blocks', get_blocks(config.BLOCKS_CACHE_SIZE), timeout=config.BLOCKS_CACHE_TIMEOUT)
    return cache.get('blocks')


def validate_input(search_string):
    if search_string.isdigit():
        if int(search_string) <= blockcount():
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
        blocks = cached_blocks()
    except Exception as e:
        print('Error retreving blocks from the local database.')
        print(e)
        pass
    return render_template('blocks.html', blocks=blocks)


@app.route('/transaction', methods=['GET'])
def show_rawtx():
    search_string = validate_input(request.values.get('txid').strip().lower())
    if search_string is None:
        print('Error: Search string was invalid.')
        return ('', 204)
    # retrieve raw transaction data
    try:
        rawtx = get_raw_tx(search_string)
    except Exception as e:
        print(e)
        print('Error: Failed to retrieve raw transaction.')
        return ('', 204)
    finally:
        response = make_response(rawtx)
        response.headers["content-type"] = "text/plain"
        return response


@app.route('/block', methods=['GET', 'POST'])
def show_block():
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
    census = stats(count=True, txs=True, height=True, diff=True)
    print(str(census['txs']) + ' transactions are indexed.')
    print('Block ' + str(census['height']) + ' is the most recent one.')
    print(str(census['count']) + ' blocks available for search.')
    print(str(census['diff']) + ' blocks seem missing from the database.')
    atexit.register(closedb)
    app.run(host='0.0.0.0', port=int(config.BIND_PORT), debug=app.config['DEBUG'])


if __name__ == '__main__':
    main()
