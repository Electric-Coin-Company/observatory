# zcash-block-observatory
Records and displays information about Zcash blocks.

Instructions
------------

Copy sendblock.py to `/usr/local/bin/sendblock` and set it executable.

Add `blocknotify=/usr/local/bin/sendblock %s` to `~/.zcash/zcash.conf`. Restart zcashd.

Run `python receiveblocks.py`. Leave it running in order to collect blocks and build the database.

Run `python showblocks.py`. This is the block observatory user interface, a Python Flask web application. It listens on http://127.0.0.1:8201.
