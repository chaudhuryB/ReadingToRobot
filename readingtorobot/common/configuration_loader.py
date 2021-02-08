"""
    Methods to load configuration files.

    [Requires Python 2.7 compatibility]
"""

import os
import json


__all__ = [
    'module_file',
    'resource_file',
    'load_config_file',
    'load_book'
]


def module_file(filename):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)


def resource_file(filename):
    return module_file("resources/{}".format(filename))


def load_config_file(path):
    if os.path.isfile(path) and path.endswith('json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError("Wrong file path: {}".format(path))


def load_book(path):
    if os.path.isfile(path) and path.endswith('txt'):
        with open(path, 'r') as f:
            return f.read().splitlines()
    else:
        raise ValueError("Wrong file path: {}".format(path))
