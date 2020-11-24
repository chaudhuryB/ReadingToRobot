import os
import json


def load_config_file(path: str) -> dict:
    if os.path.isfile(path) and path.endswith('json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError("Wrong file path: {}".format(path))