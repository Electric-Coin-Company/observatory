#!/usr/bin/python
# -*- coding: utf-8 -*-

from functools import wraps
from flask import Flask, g, abort, jsonify, render_template, request, Response, session
import config, json, os, sqlite3, sys, time

db_file = 'blocks.sqlite'
app = Flask(__name__)
app.config.from_object(config.FlaskConfig)

def get_blocks():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT * FROM blocks')
    blocks = c.fetchall()
    return blocks

@app.template_filter('timestamp')
def _jinja2_filter_timestamp(unix_epoch):
    return time.ctime(unix_epoch)

@app.route('/')
def index():
    return render_template('blocks.html', blocks = get_blocks())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int('8201'))
