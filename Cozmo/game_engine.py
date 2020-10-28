import asyncio
import copy
import cozmo
import time
from threading import Lock
from cozmo.util import degrees, distance_mm
from ..common.keyboard_control import EmotionController, feel

from constants import (
                       START_CUBE,
                       END_CUBE,
                       RED_LIGHT,
                       GREEN_LIGHT,
                       SEA_LIGHT,
                       CHOICE_TEXT,
                       )
from cozmo_listener import CozmoPlayerActions
from voiceRecognition import SpeechReco


class ReadEngine:
    def __init__(self, game_robot):
        self.robot = game_robot
        self.robot_proxy = None
        self.robot_cubes = []
        self.my_postiion = None
        self.face = None
        self.feel = feel.NEUTRAL
        self.lock = Lock()

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
        """
        Cozmo to find all three cubes and then order them in position for Rock/Paper/Scissor
        """
        self.robot_proxy = CozmoPlayerActions()

        self.read_listener = EmotionController(self.robot_proxy,
                                               self)
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

        cubes = []
        faces = []

        try:
            self.robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            """
            self.robot.drive_wheels(50, -50, duration=1)
            self.robot.drive_wheels(-100, 50, duration=1)
            self.robot.drive_wheels(50, -50, duration=1)
            """

            face = self.robot.world.wait_for_observed_face(timeout=600, include_existing=True)
            self.face = face
            self.robot_proxy.set_robot(self.robot, self.face)
            self.robot.turn_towards_face(face).wait_for_completed()
            self.robot.play_anim("anim_greeting_happy_03").wait_for_completed()
            self.robot.go_to_pose(self.my_position.pose).wait_for_completed()

        except asyncio.TimeoutError:
            print("Didn't find any face :-(")

        finally:
            # look_around.stop()
            if self.face is None:
                print("Didn't find anyone :-(")
                return False

        return True

    def do_feel(self, feel):
        with self.lock:
            self.feel = feel

    def listen_to_story(self):
        try:
            self.read_listener.game_on = True
            self.read_listener.start()
            while True:
                with self.lock:
                    f = self.feel
                if f == feel.NEUTRAL:
                    self.robot_proxy.do_listen()
                    time.sleep(1.0)
                elif f == feel.HAPPY:
                    self.robot_proxy.be_happy()
                elif f == feel.SAD:
                    self.robot_proxy.be_sad()
                elif f == feel.ANNOYED:
                    self.robot_proxy.be_annoyed()
                elif f == feel.SCARED:
                    self.robot_proxy.be_scared()
                elif f == feel.EXCITED:
                    self.robot_proxy.be_excited()
                """
                elif f == feel.SLEEPY:
                    self.robot_proxy.go_to_sleep()
                    break;
                """
                with self.lock:
                    f = feel.NEUTRAL

        except Exception as e:
            self.feel = feel.NEUTRAL
            print(e)

        except KeyboardInterrupt:
            print("\nInterrupted by user, shutting down")
            raise KeyboardInterrupt

        finally:
            if self.read_listener.game_on:
                self.read_listener.game_on = False
            self.read_listener.join()
            print("Thank you for reading to Cozmo")

            self.end_session()
            self.robot_proxy.do_fist_bump()
