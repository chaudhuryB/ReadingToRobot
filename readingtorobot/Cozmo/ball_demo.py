#!/usr/bin/python3
"""Execute a Ball Demo motion.

This motion makes Cozmo  find the ball and push it off the table.
"""
import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps


def cozmo_ball_game(robot: cozmo.robot.Robot):
    """Run the demo.

    :param robot: The robot proxy.
    """
    robot.drive_straight(distance_mm(20), speed_mmps(50)).wait_for_completed()
    robot.turn_in_place(degrees(90)).wait_for_completed()
    robot.drive_straight(distance_mm(250), speed_mmps(80)).wait_for_completed()
    robot.play_anim(name="anim_rtpkeepaway_playerno_03").wait_for_completed()


if __name__ == "__main__":
    cozmo.run_program(cozmo_ball_game)
