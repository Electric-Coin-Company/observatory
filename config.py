#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This is a configuration file for the Zcash block observatory.
"""


class ShowBlocksFlaskConfig(object):
    DEBUG = True
    TESTING = True
    TEMPLATE_DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = 'lQT0EE/XcyZrXDjCCJ/KRs3F2zKc0Ls3KAmT4y0pxp4='


class ShowBlocksConfig(object):
    BIND_PORT = 8201
    DB_FILE = 'file:blocks.sqlite?mode=ro'
    DB_ARGS = {'timeout': float(10), 'uri': bool(True), 'cached_statements': int(1024)}
    BLOCKS_CACHE_SIZE = 500
    BLOCKS_CACHE_TIMEOUT = 300


class ReceiveBlocksFlaskConfig(object):
    DEBUG = True
    TESTING = True


class ReceiveBlocksConfig(object):
    BIND_PORT = 8200
    DB_FILE = 'blocks.sqlite'
    DB_ARGS = {'timeout': float(20), 'detect_types': int(1), 'check_same_thread': bool(False)}


class BlockObservatoryConfig(object):
    START_BLOCK_HEIGHT = 0
    END_BLOCK_HEIGHT = 110483
    BLOCK_OBSERVATORY_URL = 'http://127.0.0.1:8200/'
    ZCASH_CLI_PATH = '/usr/bin/zcash-cli'


def ZcashConfig(filename='zcash.conf'):
    import os
    home = os.getenv("HOME")
    if not home:
        print('Error: $HOME not defined, so don\'t know where to look for zcash.conf')
        return None
    location = '.zcash/zcash.conf'
    filename = os.path.join(home, location)
    if not os.path.isfile(filename):
        print('Error: zcash.conf does not exist and can\'t be read.')
        return None
    else:
        try:
            f = open(filename)
            cfg = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        (key, value) = line.split('=', 1)
                        cfg[key] = value
                    except ValueError:
                        pass
            f.close()
        except (IOError, ValueError):
            print('Error: Failed to read Zcash configuration file.')
            pass
        finally:
            return cfg if cfg is not {} else None