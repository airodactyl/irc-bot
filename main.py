"""Main entry point for irc-bot
"""

import logging
import os.path
import socket
import re
import traceback
from pprint import pprint
from collections import namedtuple
from importlib import import_module, reload
from glob import glob

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('irc-bot')

IRCMessage = namedtuple('IRCMessage', ['prefix', 'command', 'args'])
PrivMessage = namedtuple('PrivMessage', ['sender', 'target', 'contents',
                                         'private'])

message_handlers = []  #: list of MessageHandler objects
plugin_modules = {}

def get_plugin_callbacks():
    """Return a list of all plugin callbacks.
    """
    for pkg in plugin_modules.values():
        reload(pkg)
    for fn in glob('plugins/*.py'):
        pkg = import_module('plugins.' + os.path.basename(os.path.splitext(fn)[0]))
        plugin_modules[pkg.__name__] = pkg
    return [pkg.callback for pkg in plugin_modules.values()]


def handle_ping(msg):
    """Play ping-pong.
    """
    return ['PONG ' + msg.args]


def connect_to_channels(_):
    """Connect to the channels after the MOTD has been sent.
    """
    response = []
    for channel in config['channels']:
        response.append('JOIN ' + channel['name'])
    return response


def handle_privmsg(msg):
    """React to the message.
    """
    response = []
    target, contents = msg.args.split(' ', 1)
    if contents[0] == ':':
        contents = contents[1:]
    msg = PrivMessage(msg.prefix, target, contents, target == config['nickname'])
    print(msg)
    for fn in get_plugin_callbacks():
        try:
            result = fn(msg)
            if result:
                response.append(result)
        except Exception as x:
            traceback.print_tb(x.__traceback__)
    return response


def handle_auth(_):
    """Handle notices.
    """
    response = []
    try:
        response.append('PASS ' + config['pass'])
    except KeyError:
        log.error("Required field 'pass' missing in config block.")
        raise KeyError
    return response


callback = {'PING': handle_ping,
            '376': connect_to_channels,
            'PRIVMSG': handle_privmsg,
            '464': handle_auth
           }


def parse_msg(message):
    """Convert the message into a nice data structure.
    """
    prefix = None
    command = None
    args = None

    if message[-1] != '\n':
        print('Message not a full line')

    pipeline = message.strip().split(' ', 2)

    if pipeline[0][0] == ':':
        prefix = pipeline.pop(0)
        prefix = prefix[1:] if prefix[0] == ':' else prefix

    command = pipeline.pop(0)

    if pipeline:
        args = pipeline.pop(0)

    return IRCMessage(prefix, command, args)


def delegate(text):
    """Run callbacks depending on the content of the line.
    """
    response = parse_msg(text)
    if response.command in callback:
        return callback[response.command](response)
    else:
        return []


def main():
    """Main
    """
    s = socket.socket()
    try:
        s.connect((config['server'], config['port']))
        s.send('USER {username} . . :{realname}\r\n'.format(**config).encode())
        s.send('NICK {nickname}\r\n'.format(**config).encode())

        f = s.makefile()
        while True:
            line = f.readline()
            log.debug("<-- {}".format(line.strip()))
            responses = delegate(line)
            if responses:
                for response in responses:
                    log.debug("--> {}".format(response))
                    s.send((response + '\r\n').encode())

    except KeyboardInterrupt:
        s.send('QUIT :bye\r\n'.encode())
        s.close()
        print('onnection Closed')


if __name__ == '__main__':
    servers = config.read_config('servers.yaml')
    plugins = config.read_config('plugins.yaml')
    config = servers['rizon']
    main()
