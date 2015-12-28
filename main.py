"""Main entry point for irc-bot
"""

import asyncio
from argparse import ArgumentParser
import socket
import sys


@asyncio.coroutine
def reads(reader):
    while True:
        l = yield from reader.readline()
        print(l)


@asyncio.coroutine
def co(rw):
    rw['reader'], rw['writer'] = yield from \
            asyncio.open_connection(host='irc.rizon.net', port=6667)


def main():
    print('1')
    loop = asyncio.get_event_loop()
    rw = {}
    loop.run_until_complete(co(rw))
    login(rw['writer'])
    loop.run_until_complete(reads(rw['reader']))
    print(2)


if __name__ == '__main__':
    main()
