"""Configuration file management for irc-bot.
"""

import yaml

def read_config(file='config.yaml'):
    """Read a configuration file.
    """
    return yaml.load(open(file))
