import asyncio
import copy
import cozmo
import time
from cozmo.util import degrees, distance_mm, Pose
from cozmo import event

from asyncio.locks import Lock
from random import randint, choice

from game_cubes import BlinkyCube


cozmo.world.World.light_cube_factory = BlinkyCube

class CozmoPlayerActions(object):
    """
    A singleton class defining how cozmo will act
    """

    __instance = None

    def __new__(cls):
      if not CozmoPlayerActions.__instance:
          CozmoPlayerActions.__instance = object.__new__(cls)
          CozmoPlayerActions.__instance.robot = None
          CozmoPlayerActions.__instance.face = None
      return  CozmoPlayerActions.__instance

    def set_robot(self, game_robot, face):
        self.robot = game_robot
        self.face = face
        self.last_head_position = cozmo.robot.MAX_HEAD_ANGLE

    def be_sad(self):
        self.play_anim(
            choice([ 'anim_rtpmemorymatch_no_01',
                     'anim_speedtap_playerno_01',
                     'anim_memorymatch_failhand_02',
                     'anim_energy_cubenotfound_02'
                    ]))

    def be_happy(self):
        self.play_anim(
            choice([ 'anim_poked_giggle',
                     'anim_reacttoblock_happydetermined_01',
                     'anim_memorymatch_failhand_player_02',
                     'anim_pyramid_reacttocube_happy_low_01',
                     'anim_pyramid_reacttocube_happy_mid_01',
                     'anim_pyramid_reacttocube_happy_high_02',
                    ]))

    def be_annoyed(self):
        self.play_anim(
            choice([ 'anim_memorymatch_failhand_01',
                     'anim_reacttoblock_frustrated_01',
                     'anim_pyramid_reacttocube_frustrated_low_01',
                     'anim_reacttoblock_frustrated_int2_01',
                    ]))

    def be_scared(self):
        self.play_anim(
            choice([ 'anim_rtpmemorymatch_no_01',
                     'anim_speedtap_playerno_01',
                     'anim_memorymatch_failhand_02',
                     'anim_energy_cubenotfound_02',
                    ]))

    def be_excited(self):
        self.play_anim(
            choice([ 'anim_speedtap_wingame_intensity03_01',
                     'anim_codelab_chicken_01',
                    ]))

    def do_listen(self):
        # Do little look down/up nods:
        play_wait = randint(0,3)
        if play_wait==0:
            print("Looking away")
            self.robot.set_head_angle(degrees(0)).wait_for_completed()
            self.play_anim(
                choice([ 'anim_speedtap_wait_short',
                         'anim_speedtap_wait_medium',
                         'anim_speedtap_wait_medium_02',
                         'anim_speedtap_wait_medium_03',
                         'anim_speedtap_wait_long',
                        ]))
        else:
            print("Looking at face")
            if self.face:
                # start turning towards the face
                self.robot.set_head_angle(self.last_head_position).wait_for_completed()
                self.robot.turn_towards_face(self.face).wait_for_completed()
                self.last_head_position = self.robot.head_angle

            time.sleep(0.5)

    def go_to_sleep(self):
        print("That was a vey soothing story. Cozmo has just dozed off")
        self.robot.play_anim('anim_gotosleep_sleeping_01').wait_for_completed()

    def start_free_play(self):
        print("What is Cozmo up to?")
        self.robot.start_freeplay_behaviors()
        time.sleep(90)
        self.robot.stop_freeplay_behaviors()

    def play_anim(self, anim):
        try:
            self.robot.play_anim(anim).wait_for_completed()
        except:
            print("Error while playing animation: " + anim)

    @event.oneshot
    def handle_fist_bump(self, event):
        print( event)
        self.fist_bump_success = True

    def do_fist_bump(self):
        print("Fist bump?")
        wait_time = 10.0
        self.fist_bump_success = False

        self.robot.add_event_handler(cozmo.world.EvtRobotMovedBish, self.handle_fist_bump)
        self.robot.move_lift(5)
        time.sleep(.2)
        self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestOnce).wait_for_completed()


        while not self.fist_bump_success and wait_time > 0:
            time.sleep(0.5)
            wait_time -= 0.5

        if not self.fist_bump_success:
            # No fist bumo yet request again
            wait_time = 10.0
            print("Please fist bump")
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestRetry).wait_for_completed()
            while not self.fist_bump_success and wait_time > 0:
                time.sleep(0.5)
                wait_time -= 0.5

        if self.fist_bump_success:
            print("hehe fist bumped")
            self.robot.move_lift(-3)
            time.sleep(.2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpSuccess).wait_for_completed()
        else:
            print("Cozmo is sad, no fist bump")
            self.robot.move_lift(-3)
            time.sleep(2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpLeftHanging).wait_for_completed()

