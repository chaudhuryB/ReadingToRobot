"""
    Methods to load configuration files.
"""

import os
import json


def resource_file(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources/{}".format(filename))


def load_config_file(path: str) -> dict:
    if os.path.isfile(path) and path.endswith('json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError("Wrong file path: {}".format(path))


def load_book(path: str) -> list:
    if os.path.isfile(path) and path.endswith('txt'):
        with open(path, 'r') as f:
            return f.read().splitlines()
    else:
        raise ValueError("Wrong file path: {}".format(path))
