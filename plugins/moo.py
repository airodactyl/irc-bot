import re
def callback(msg):
    recipient = re.match(r'^[^!]*', msg.sender).group(0) if msg.private else msg.target
    if 'moo' in msg.contents:
        return 'PRIVMSG {} :{}'.format(recipient, 'moo!!')
