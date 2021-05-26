"""
    Methods to load configuration files.

    [Requires Python 2.7 compatibility]
"""

import json
import os


__all__ = [
    'load_book',
    'load_config_file',
    'module_file',
    'resource_file',
]


def load_book(path):
    """ Open text file in given path. """
    if os.path.isfile(path) and path.endswith('txt'):
        with open(path, 'r') as f:
            return f.read().splitlines()
    else:
        raise ValueError("Wrong file path: {}".format(path))


def load_config_file(path):
    """ Open JSON file in given path. """
    if os.path.isfile(path) and path.endswith('json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError("Wrong file path: {}".format(path))


def module_file(filename):
    """ Find path to a file in the package. """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)


def resource_file(filename):
    """ Find path to file in the resources folder of the package. """
    return module_file("resources/{}".format(filename))
