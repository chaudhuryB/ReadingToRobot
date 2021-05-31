"""
    Game engine.
"""

import copy
import logging
import time
from cozmo.util import degrees

from ..common import Feel, FeelingReaction, MQTTManager
from .constants import END_CUBE
from .cozmo_listener import CozmoPlayerActions


class ReadEngine:
    def __init__(self, game_robot, mqtt_ip=None, timeout=20):
        self.robot = game_robot
        self.robot_proxy = CozmoPlayerActions()
        self.robot_cubes = []
        self.my_postiion = None
        self.feel = Feel.NEUTRAL
        self.logger = logging.getLogger(name=__name__)
        self.feel_control = FeelingReaction(self)

        # Connection to command server
        self.mqtt_client = MQTTManager("cozmo", self.robot_proxy.stop, self.feel_control.process_text, timeout, mqtt_ip)

    def end_session(self):
        for cube in self.robot_cubes:
            cube.start_light_chaser(END_CUBE)

        time.sleep(3)
        for cube in self.robot_cubes:
            cube.stop_light_chaser()
            cube.set_lights_off()

    def cozmo_setup_game(self):
        # Wait for mqtt connection
        self.mqtt_client.start()

        self.my_position = self.robot.world.create_custom_fixed_object(copy.deepcopy(self.robot.pose),
                                                                       1,
                                                                       1,
                                                                       1,
                                                                       use_robot_origin=False)
        self.robot.set_head_angle(degrees(0)).wait_for_completed()
        self.robot.move_lift(-3)
        time.sleep(0.5)

        return

    def do_feel(self, feel):
        self.robot_proxy.do_feel(feel)

    def listen_to_story(self):
        try:
            # Launch Listener and Robot threads.
            self.robot_proxy.start(self.robot)
            self.robot_proxy.join()
        except KeyboardInterrupt:
            self.logger.info("\nInterrupted by user, shutting down")
            raise KeyboardInterrupt

        finally:
            self.logger.info("Thank you for reading to Cozmo")
            self.end_session()
            self.robot_proxy.stop()
