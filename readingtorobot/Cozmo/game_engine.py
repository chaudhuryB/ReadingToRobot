"""
    Game engine.
"""

import asyncio
import copy
import logging
import time
import cozmo

from cozmo.util import degrees
import paho.mqtt.client as mqtt

from ..common.feeling_expression import Feel, FeelingReaction
from .constants import START_CUBE, END_CUBE
from .cozmo_listener import CozmoPlayerActions


class ReadEngine:
    def __init__(self, game_robot, keyboard_control=False, mqtt_ip=None, timeout=20):
        self.robot = game_robot
        self.robot_proxy = None
        self.robot_cubes = []
        self.my_postiion = None
        self.feel = Feel.NEUTRAL
        self.logger = logging.getLogger(name=__name__)
        self.keyboard_control = keyboard_control
        self.feel_control = FeelingReaction(self)

        # Connection to command server
        self.mqtt_client = mqtt.Client("cozmo")
        self.mqtt_client.message_callback_add("cozmo/stop", self.stop_callback)
        self.mqtt_client.message_callback_add("speech/cmd", self.process_text)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.connect(mqtt_ip)
        self.mqtt_client.subscribe("cozmo/stop", 0)
        self.mqtt_client.subscribe("speech/cmd", 0)
        self.mqtt_timeout = timeout
        self.connected_flag = False
        self.mqtt_client.loop_start()

    def tap_ready(self):
        player_tapped = False
        light_cube_list = [cozmo.objects.LightCube1Id, cozmo.objects.LightCube2Id, cozmo.objects.LightCube3Id]
        for lightcube_id in light_cube_list:
            cube = self.robot.world.light_cubes.get(lightcube_id)
            self.robot_cubes.append(cube)
            cube.start_light_chaser(START_CUBE)

        try:
            tapped_event = self.robot.world.wait_for(cozmo.objects.EvtObjectTapped, timeout=120)
            if tapped_event:
                player_tapped = True

        except asyncio.TimeoutError:
            pass

        for cube in self.robot_cubes:
            cube.stop_light_chaser()
            cube.set_lights_off()
        return player_tapped

    def end_session(self):
        for cube in self.robot_cubes:
            cube.start_light_chaser(END_CUBE)

        time.sleep(3)
        for cube in self.robot_cubes:
            cube.stop_light_chaser()
            cube.set_lights_off()

    def cozmo_setup_game(self):
        # Wait for mqtt connection
        for _ in range(self.mqtt_timeout):
            if self.connected_flag:
                break
            time.sleep(1)
        else:
            self.logger.error("MQTT connection timed out, exiting.")

        self.robot_proxy = CozmoPlayerActions()

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

    def stop_callback(self, cli, obj, msg):
        self.logger.info("Stop message recieved: {}".format(msg.topic))
        self.robot_proxy.stop()
        # Add mqtt response saying we finished.
        self.logger.info("Sending response.")
        self.mqtt_client.publish("cozmo/stopped_clean", "0")
        time.sleep(5)
        self.mqtt_client.loop_stop()

    def process_text(self, cli, obj, msg):
        if not self.keyboard_control:
            self.feel_control.process_text(msg.payload.decode('ascii'))
        else:
            self.logger.warning("Keyboard control is enabled, speech msg ignored: {}, {}, {}".format(msg.topic,
                                                                                                     msg.qos,
                                                                                                     msg.payload))

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected_flag = True
            self.logger.info("Connected to MQTT broker.")
            self.mqtt_client.publish("cozmo/started", 1)
        else:
            self.logger.error("Bad connection to mqtt, returned code: {}".format(rc))
            self.mqtt_client.publish("cozmo/started", 0)
