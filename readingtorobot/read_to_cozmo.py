#!/usr/bin/python3

import logging

import cozmo
from .Cozmo.game_engine import ReadEngine


def cozmo_read_game(robot: cozmo.robot.Robot):
    # Initialize all the game engines screens and listners
    read_game = ReadEngine(robot)
    if read_game.tap_ready():
        if read_game.cozmo_setup_game():
            read_game.listen_to_story()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s:%(levelname)s:\033[32m%(name)s\033[0m: %(message)s', level=logging.DEBUG)
    cozmo.run_program(cozmo_read_game)
