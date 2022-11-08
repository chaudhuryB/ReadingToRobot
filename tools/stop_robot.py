"""
    Attempt to stop the robot process cleanly, if it times out, it will forcefully kill the process.
"""

import argparse
import sys
import time

import paho.mqtt.client as mqtt


def s_callback(cli, obj, msg):
    """Notify the confirmation of the robot stopping cleanly."""
    print("Recieved message: {} {} {}".format(msg.topic, msg.qos, msg.payload))
    sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("robot", type=str, help="Name of the robot to stop.")
    parser.add_argument("--robotIP", type=str, default="127.0.0.1", help="IP address of the robot")

    args = parser.parse_args()
    robot = args.robot.lower()
    robot_ip = args.robotIP

    # First attemp to stop the robot cleanly.
    mqttc = mqtt.Client()
    mqttc.message_callback_add("{}/stopped_clean".format(robot), s_callback)
    mqttc.connect("10.204.38.100")
    mqttc.subscribe("{}/stopped_clean".format(robot), 0)
    mqttc.loop_start()

    mqttc.publish("{}/stop".format(robot), "stop")

    # Wait some time to see if the robot responds to the command.
    time.sleep(30)

    # TODO: Otherwise, call the kill script
