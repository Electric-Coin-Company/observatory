#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Common functions to the Zcash Block Observatory project.
"""
import getpass
import json
import os
import psutil
import subprocess
import sys
from config import BlockObservatoryConfig as config


def blockcount():
    try:
        output = subprocess.check_output([config.ZCASH_CLI_PATH, 'getblockcount'])
    except Exception as e:
        print(e)
        print('Error: Can\'t communicate with or parse JSON from Zcash RPC Interface.')
        return False
    return int(output)


def zcashd_access_test(proc):
    current_user = str(getpass.getuser())
    try:
        os.kill(proc['pid'], 0)
        if proc['username'] == current_user and isinstance(blockcount(), int):
            print('Success: found zcashd is running as ' + current_user + ' allowing RPC interface access.')
            return True
    except Exception as e:
        print(e)
        print('Error: This zcashd does not seem to be running as the user of this script.')
        return False


def is_zcashd_running():
    if sys.version_info[0] == 2:
        zcashd_procs = filter(lambda p: p.name() == "zcashd", psutil.process_iter())
    elif sys.version_info[0] == 3:
        zcashd_procs = [p for p in psutil.process_iter() if p.name() == "zcashd"]
    if zcashd_procs is not [] and len(zcashd_procs) >= 1:
        procs = [proc.as_dict(attrs=['pid', 'username']) for proc in zcashd_procs]
        for proc in procs:
            print("zcashd running with pid %d as user %s" % (proc['pid'], proc['username']))
            while zcashd_access_test(proc):
                return True
    else:
        print('Error: Could not find an accessible running instance of zcashd on this system.')
        return False


def get_block(block_height):
    try:
        output = subprocess.check_output([config.ZCASH_CLI_PATH, 'getblock', block_height])
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve block number ' + block_height + ' from zcashd.')
        return None
    return json.loads((output.decode('utf-8')))


def optimizedb(conn):
    c = conn.cursor()
    c.execute('PRAGMA journal_mode = WAL')
    c.execute('PRAGMA page_size = 8096')
    c.execute('PRAGMA temp_store = 2')
    c.execute('PRAGMA synchronous = 0')
    c.execute('PRAGMA cache_size = 8192000')
    conn.commit()
    return


def zcash(cmd):
    zcash = subprocess.Popen(['/usr/bin/zcash-cli', cmd], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = zcash.communicate()[0]
    return output
