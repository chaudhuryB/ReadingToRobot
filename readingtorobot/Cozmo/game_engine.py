"""
    Game engine.
"""

import asyncio
import copy
import logging
import time
import cozmo

from cozmo import robot
from cozmo.util import degrees, distance_mm, speed_mmps
import paho.mqtt.client as mqtt

from ..common.feeling_declaration import Feel
from ..common.keyboard_control import EmotionController
from ..common.speech_conn import DetachedSpeechReco
from .constants import START_CUBE, END_CUBE
from .cozmo_listener import CozmoPlayerActions


class ReadEngine:
    def __init__(self, game_robot, keyboard_control=False, mqtt_ip=None, timeout=20):
        self.robot = game_robot
        self.robot_proxy = None
        self.robot_cubes = []
        self.my_postiion = None
        self.face = None
        self.feel = Feel.NEUTRAL
        self.logger = logging.getLogger(name=__name__)
        self.keyboard_control = keyboard_control
        self.feel_control = EmotionController(self) if keyboard_control else DetachedSpeechReco(self)

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
            self.robot_proxy.stop()

        self.robot_proxy = CozmoPlayerActions()

        if self.robot.is_on_charger:
            self.robot.DriveOffChargerContacts().wait_for_completed()
            robot.drive_straight(distance_mm(800), speed_mmps(500)).wait_for_completed()

        self.my_position = self.robot.world.create_custom_fixed_object(copy.deepcopy(self.robot.pose),
                                                                       1,
                                                                       1,
                                                                       1,
                                                                       use_robot_origin=False)
        self.robot.set_head_angle(degrees(0)).wait_for_completed()
        self.robot.move_lift(-3)
        time.sleep(0.5)

        try:
            # Greeting action. Will identify a new face and acknowledge it before starting the listening/reaction
            # thread.
            self.robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            """
            self.robot.drive_wheels(50, -50, duration=1)
            self.robot.drive_wheels(-100, 50, duration=1)
            self.robot.drive_wheels(50, -50, duration=1)
            """

            face = self.robot.world.wait_for_observed_face(timeout=600, include_existing=True)
            self.face = face
            self.robot.turn_towards_face(face).wait_for_completed()
            self.robot.play_anim("anim_greeting_happy_03").wait_for_completed()
            self.robot.go_to_pose(self.my_position.pose).wait_for_completed()

        except asyncio.TimeoutError:
            self.logger.warning("Didn't find any face :-(")

        finally:
            # look_around.stop()
            if self.face is None:
                self.logger.warning("Didn't find anyone :-(")
                return False

        return True

    def do_feel(self, feel):
        self.robot_proxy.do_feel(feel)

    def listen_to_story(self):
        try:
            # Launch Listener and Robot threads.
            self.robot_proxy.start(self.robot, self.face)
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
        else:
            self.logger.error("Bad connection to mqtt, returned code: {}".format(rc))
