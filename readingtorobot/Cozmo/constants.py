"""Constant variables used for Cozmo."""

import cozmo

START_CUBE = 0
END_CUBE = 1

NEUTRAL = 0
HAPPY = 1
SAD = 2
ANNOYED = 3
SCARED = 4
SLEEPY = 5
EXCITED = 6

CHOICE_TEXT = ["Rock", "Paper", "Scissor"]

RED_LIGHT = cozmo.lights.red_light
BLUE_LIGHT = cozmo.lights.blue_light
GREEN_LIGHT = cozmo.lights.green_light
YELLOW_LIGHT = cozmo.lights.Light(cozmo.lights.Color(rgb=(255, 255, 0)), cozmo.lights.off)
PINK_LIGHT = cozmo.lights.Light(cozmo.lights.Color(rgb=(255, 0, 255)), cozmo.lights.off)
SEA_LIGHT = cozmo.lights.Light(cozmo.lights.Color(rgb=(0, 255, 255)), cozmo.lights.off)
PURPLE_LIGHT = cozmo.lights.Light(cozmo.lights.Color(rgb=(65, 0, 130)), cozmo.lights.off)
