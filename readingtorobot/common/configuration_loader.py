"""
Methods to load configuration files.

[Requires Python 2.7 compatibility]
"""

import json
import os


__all__ = [
    "load_book",
    "load_config_file",
    "module_file",
    "resource_file",
]


def load_book(path):
    """Open text file in given path.

    :param path: Path to the book description file.
    :type path: str
    :return: List of all lines in the given file.
    :rtype: List[str]
    """
    if os.path.isfile(path) and path.endswith("txt"):
        with open(path, "r") as f:
            return f.read().splitlines()
    else:
        raise ValueError("Wrong file path: {}".format(path))


def load_config_file(path):
    """Open JSON file in given path.

    :param path: Path to the JSON file.
    :type path: str
    :return: Dictionary with loaded JSON data.
    :rtype: Dict|List
    """
    if os.path.isfile(path) and path.endswith("json"):
        with open(path, "r") as f:
            return json.load(f)
    else:
        raise ValueError("Wrong file path: {}".format(path))


def module_file(filename):
    """Find path to a file in the package.

    :param filename: Path to the file relative to the package.
    :type filename: str
    :return: Absolute path to the required file.
    :rtype: str
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)


def resource_file(filename):
    """Find path to file in the resources folder of the package.

    :param filename: Path to resource file.
    :type filename: str
    :return: Absolute path to the module file.
    :rtype: str
    """
    return module_file("resources/{}".format(filename))
