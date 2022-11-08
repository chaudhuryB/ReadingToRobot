"""
    Game engine.
"""

import copy
import logging
import time
from typing import Optional
from cozmo.util import degrees

from ..common import Feel, FeelingReaction, MQTTManager
from .constants import END_CUBE
from .cozmo_listener import CozmoPlayerActions
from .cozmo_world import Robot


class ReadEngine:
    """Manager for reading with robot interaction."""

    def __init__(self, game_robot: Robot, mqtt_ip: Optional[str] = None, timeout: int = 20):
        """Initialize engine."""
        self._robot = game_robot
        self._robot_proxy = CozmoPlayerActions()
        self._robot_cubes = []
        self._my_position = None
        self._feel = Feel.NEUTRAL
        self._logger = logging.getLogger(name=__name__)
        self._feel_control = FeelingReaction(self)

        # Connection to command server
        self._mqtt_client = MQTTManager(
            "cozmo", self._robot_proxy.stop, self._feel_control.process_text, timeout, mqtt_ip
        )

    def end_session(self):
        """Stop experiment."""
        for cube in self._robot_cubes:
            cube.start_light_chaser(END_CUBE)

        time.sleep(3)
        for cube in self._robot_cubes:
            cube.stop_light_chaser()
            cube.set_lights_off()

    def cozmo_setup_game(self):
        """Set up experiment."""
        # Wait for mqtt connection
        self._mqtt_client.start()

        self._my_position = self._robot.world.create_custom_fixed_object(
            copy.deepcopy(self._robot.pose), 1, 1, 1, use_robot_origin=False
        )
        self._robot.set_head_angle(degrees(0)).wait_for_completed()
        self._robot.move_lift(-3)
        time.sleep(0.5)

    def do_feel(self, feel: Feel):
        """Execute feeling animation."""
        self._robot_proxy.do_feel(feel)

    def listen_to_story(self):
        """Run experiment."""
        try:
            # Launch Listener and Robot threads.
            self._robot_proxy.start(self._robot)
            self._robot_proxy.join()
        except KeyboardInterrupt:
            self._logger.info("\nInterrupted by user, shutting down")
            raise KeyboardInterrupt

        finally:
            self._logger.info("Thank you for reading to Cozmo")
            self.end_session()
            self._robot_proxy.stop()
