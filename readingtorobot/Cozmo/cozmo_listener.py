"""
    Thread managing the robot animations.
"""

import asyncio
import logging
import time
from random import randint, choice
from threading import Thread
from queue import Queue, Empty

import cozmo
from cozmo.util import degrees
from cozmo import event

from .game_cubes import BlinkyCube
from ..common.feeling_declaration import Feel


cozmo.world.World.light_cube_factory = BlinkyCube


class CozmoPlayerActions(Thread):
    """
        Thread controlling the robot actions.
    """
    QUEUE_TIMEOUT = 0.1

    def __init__(self):
        super().__init__()
        self.queue = Queue()

    def start(self, game_robot):
        self.name = 'Robot'
        self.robot = game_robot
        self.face = None
        self.last_head_position = cozmo.robot.MAX_HEAD_ANGLE
        self.running_animation = None
        self.running = True
        self.logger = logging.getLogger(name=__name__)
        super().start()

    def stop(self):
        self.running = False
        if self.is_alive():
            self.join()

    def run(self):
        while self.running:
            if not self.face:
                try:
                    self.robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
                    self.face = self.robot.world.wait_for_observed_face(timeout=1, include_existing=True)
                    self.robot.turn_towards_face(self.face).wait_for_completed()
                except asyncio.TimeoutError:
                    self.logger.warning("Didn't find any face.")

            try:
                f = self.queue.get(timeout=self.QUEUE_TIMEOUT)
            except Empty:
                self.do_listen()
                continue

            if f == Feel.HAPPY:
                self.be_happy()
            elif f == Feel.SAD:
                self.be_sad()
            elif f == Feel.ANNOYED:
                self.be_annoyed()
            elif f == Feel.SCARED:
                self.be_scared()
            elif f == Feel.EXCITED:
                self.be_excited()

    def do_feel(self, feel):
        self.queue.put(feel)
        if self.running_animation is not None:
            self.running_animation.abort()

    def be_sad(self):
        self.play_anim(
            choice(['anim_rtpmemorymatch_no_01',
                    'anim_speedtap_playerno_01',
                    'anim_memorymatch_failhand_02',
                    'anim_energy_cubenotfound_02']))

    def be_happy(self):
        self.play_anim(
            choice(['anim_poked_giggle',
                    'anim_reacttoblock_happydetermined_01',
                    'anim_memorymatch_failhand_player_02',
                    'anim_pyramid_reacttocube_happy_low_01',
                    'anim_pyramid_reacttocube_happy_mid_01',
                    'anim_pyramid_reacttocube_happy_high_02']))

    def be_annoyed(self):
        self.play_anim(
            choice(['anim_memorymatch_failhand_01',
                    'anim_reacttoblock_frustrated_01',
                    'anim_pyramid_reacttocube_frustrated_low_01',
                    'anim_reacttoblock_frustrated_int2_01']))

    def be_scared(self):
        self.play_anim(
            choice(['anim_rtpmemorymatch_no_01',
                    'anim_speedtap_playerno_01',
                    'anim_memorymatch_failhand_02',
                    'anim_energy_cubenotfound_02']))

    def be_excited(self):
        self.play_anim(
            choice(['anim_speedtap_wingame_intensity03_01',
                    'anim_codelab_chicken_01']))

    def do_listen(self):
        # Do little look down/up nods:
        play_wait = randint(0, 3)
        if play_wait == 0:
            self.logger.debug("Looking away")
            self.robot.set_head_angle(degrees(0)).wait_for_completed()
            self.play_anim(
                choice(['anim_speedtap_wait_short',
                        'anim_speedtap_wait_medium',
                        'anim_speedtap_wait_medium_02',
                        'anim_speedtap_wait_medium_03',
                        'anim_speedtap_wait_long']))
        else:
            self.logger.debug("Looking at face")
            if self.face:
                # start turning towards the face
                self.robot.set_head_angle(self.last_head_position).wait_for_completed()
                self.robot.turn_towards_face(self.face).wait_for_completed()
                self.last_head_position = self.robot.head_angle

            time.sleep(0.5)

    def go_to_sleep(self):
        self.logger.info("That was a vey soothing story. Cozmo has just dozed off")
        self.robot.play_anim('anim_gotosleep_sleeping_01').wait_for_completed()

    def start_free_play(self):
        self.logger.info("What is Cozmo up to?")
        self.robot.start_freeplay_behaviors()
        time.sleep(90)
        self.robot.stop_freeplay_behaviors()

    def play_anim(self, anim):
        try:
            self.running_animation = self.robot.play_anim(anim)
            self.running_animation.wait_for_completed()
        except Exception as e:
            self.logger.warning("Error while playing animation \'{}\': {}".format(anim, e))
            pass

    @event.oneshot
    def handle_fist_bump(self, event):
        self.logger.info(event)
        self.fist_bump_success = True

    def do_fist_bump(self):
        self.logger.info("Fist bump?")
        wait_time = 10.0
        self.fist_bump_success = False

        # This event EvtRobotMovedBish was added to the cozmo.world.py in site-packages specifically for this
        # It is dispatched when the world receives the robot delocalized message because that is what "fist bumping"
        # tiny Cozmo does.
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
            self.logger.info("Please fist bump")
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestRetry).wait_for_completed()
            while not self.fist_bump_success and wait_time > 0:
                time.sleep(0.5)
                wait_time -= 0.5

        if self.fist_bump_success:
            self.logger.info("hehe fist bumped")
            self.robot.move_lift(-3)
            time.sleep(.2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpSuccess).wait_for_completed()
        else:
            self.logger.info("Cozmo is sad, no fist bump")
            self.robot.move_lift(-3)
            time.sleep(2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpLeftHanging).wait_for_completed()
