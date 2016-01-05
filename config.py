"""Configuration file management for irc-bot.
"""

import yaml

def read_config(file):
    """Read a configuration file.
    """
    return yaml.load(open(file))
