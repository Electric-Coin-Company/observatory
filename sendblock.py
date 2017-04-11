#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, os, requests, subprocess, sys, time
block_observatory_url = 'http://127.0.0.1:8200/'

def zcash(block_hash):
    zcash = subprocess.Popen(['/usr/bin/zcash-cli', 'getblock', block_hash], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = zcash.communicate()[0]
    return json.loads(output)

def main():
    timestamp = int(time.time())
    block_hash = str(sys.argv[1])
    block = zcash(block_hash)
    block['arrivaltime'] = timestamp
    session = requests.session()
    session.headers.update({'Content-Type': 'application/json'})
    r = session.post(block_observatory_url, json=block)
    r.raise_for_status()

if __name__ == '__main__':
    main()
