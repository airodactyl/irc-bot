"""Main entry point for irc-bot
"""

import socket
from pprint import pprint
from configparser import ConfigParser
from collections import namedtuple

IRCMessage = namedtuple('IRCMessage', ['prefix', 'command', 'args'])


def handle_ping(msg):
    """Play ping-pong.
    """
    return 'PONG {}'.format(' '.join(msg.args))


callback = {'PING': handle_ping
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
        args = pipeline

    return IRCMessage(prefix, command, args)


def delegate(text):
    """Run callbacks depending on the content of the line.
    """
    response = parse_msg(text)
    try:
        return callback[response.command](response)
    except KeyError:
        return


def main():
    """Main
    """
    config = ConfigParser()
    config.read('config.ini')
    config = config[config.sections()[0]]

    s = socket.socket()
    try:
        s.connect((config['server'], config.getint('port')))
        s.send('USER {} . . :{}\r\n'
               .format(config['username'], config['realname'])
               .encode())
        s.send('NICK {}\r\n'
               .format(config['nickname'])
               .encode())
        s.send('JOIN {}\r\n'
               .format(config['channel'])
               .encode())

        f = s.makefile()
        while True:
            line = f.readline()
            print(repr(line), file=open('log', 'a'))
            response = delegate(line)
            if response:
                print(">>>>> {}".format(response), file=open('log', 'a'))
                s.send((response + '\r\n').encode())

    except KeyboardInterrupt:
        s.send('QUIT :bye\r\n'.encode())
        s.close()
        print('onnection Closed')


if __name__ == '__main__':
    main()
