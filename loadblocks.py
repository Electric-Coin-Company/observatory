#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import requests

from helpers import blockcount, is_zcashd_running, get_block
from config import BlockObservatoryConfig as config


def parse_cmd_args():
    description = """
Allows one to specify the block range to import via START_BLOCK_HEIGHT and END_BLOCK_HEIGHT
Example:
     export START_BLOCK_HEIGHT=1234
     export END_BLOCK_HEIGHT=12345678
     ./loadblocks.py
or...
     ./loadblocks.py --start 1234 --end 12345678
"""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--start', type=int, default=os.environ.get('START_BLOCK_HEIGHT', config.START_BLOCK_HEIGHT),
                        required=False, help="Block number to begin import from")
    parser.add_argument('--end', type=int, default=os.environ.get('END_BLOCK_HEIGHT', config.END_BLOCK_HEIGHT),
                        required=False, help="Block number to stop importing at")
    return parser.parse_args()


def main():
    if not is_zcashd_running():
        sys.exit(1)

    args = parse_cmd_args()
    start_point = args.start
    end_point = args.end
    num_blocks = blockcount() if isinstance(blockcount(), int) else None

    if num_blocks is not None:
        session = requests.session()
        session.headers.update({'Content-Type': 'application/json'})
        for x in range(start_point if (start_point > 0) else start_point,
                       end_point if (end_point < num_blocks) else end_point):
            block = get_block(str(x))
            if block is not None:
                r = session.post(config.BLOCK_OBSERVATORY_URL, json=block)
                r.raise_for_status()
                print('Uploaded block ' + str(x) + '.')
            else:
                continue
    else:
        print('Error: Can\'t retrieve blocks from zcashd.')
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
