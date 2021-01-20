#!/usr/bin/python
#
# Main script for Reading With Robots and MiRo
#

import argparse
import logging
import os

from .MiRo.robot_manager import RobotManager


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s:%(levelname)s:\033[32m%(name)s\033[0m: %(message)s', level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('animation_dir', nargs='?', default=os.getcwd())
    args = parser.parse_args()

    # instantiate
    app = RobotManager(animation_dir=args.animation_dir)

    # execute
    app.loop()

    # terminate
    app.term()
