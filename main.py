"""Main entry point for irc-bot
"""

import socket
import re
from pprint import pprint
from collections import namedtuple

import config

IRCMessage = namedtuple('IRCMessage', ['prefix', 'command', 'args'])
MessageHandler = namedtuple('MessageHandler', ['pattern', 'callback'])


message_handlers = []  #: list of MessageHandler objects


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
    for handler in message_handlers:
        if re.match(handler.pattern, contents):
            response.append(handler.callback(contents))
    return response


def handle_auth(_):
    """Handle notices.
    """
    response = []
    response.append('PASS a:a')
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
        pprint(message)

    pipeline = message.strip().split(' ', 2)

    if pipeline[0][0] == ':':
        prefix = pipeline.pop(0)

    command = pipeline.pop(0)

    if pipeline:
        args = pipeline.pop(0)

    return IRCMessage(prefix, command, args)


def delegate(text):
    """Run callbacks depending on the content of the line.
    """
    response = parse_msg(text)
    try:
        return callback[response.command](response)
    except KeyError:
        return []


def main():
    """Main
    """
    config = servers['rizon']
    s = socket.socket()
    try:
        s.connect((config['server'], config['port']))
        s.send('USER {username} . . :{realname}\r\n'.format(**config).encode())
        s.send('NICK {nickname}\r\n'.format(**config).encode())

        f = s.makefile()
        while True:
            line = f.readline()
            print(repr(line), file=open('log', 'a'))
            responses = delegate(line)
            if responses:
                for response in responses:
                    print(">>>>> {}".format(response), file=open('log', 'a'))
                    s.send((response + '\r\n').encode())

    except KeyboardInterrupt:
        s.send('QUIT :bye\r\n'.encode())
        s.close()
        print('onnection Closed')


if __name__ == '__main__':
    servers = config.read_config('servers.yaml')
    plugins = config.read_config('plugins.yaml')
    main()
