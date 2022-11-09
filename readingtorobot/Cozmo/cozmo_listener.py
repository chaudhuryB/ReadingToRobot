"""Thread managing the robot animations."""

import asyncio
import logging
import time
from random import choice, randint
from threading import Thread
from queue import Empty, Queue

import cozmo
from cozmo import event
from cozmo.util import degrees

from .game_cubes import BlinkyCube
from .cozmo_world import Robot, EvtRobotMovedBish
from ..common import Feel


cozmo.world.World.light_cube_factory = BlinkyCube


class CozmoPlayerActions(Thread):
    """Thread controlling the robot actions."""

    QUEUE_TIMEOUT = 0.1

    def __init__(self) -> None:
        """Initialize CozmoPlayerActions."""
        super().__init__()
        self._queue = Queue()

    def start(self, game_robot: Robot):
        """Start thread.

        :param game_robot: The robot proxy.
        """
        self.name = "Robot"
        self._robot = game_robot
        self._face = None
        self._last_head_position = cozmo.robot.MAX_HEAD_ANGLE
        self._running_animation = None
        self._running = True
        self._logger = logging.getLogger(name=__name__)
        super().start()

    def stop(self):
        """Stop thread."""
        self._running = False
        if self.is_alive():
            self.join()

    def run(self):
        """Run thread task."""
        while self._running:
            if not self._face:
                try:
                    self._robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
                    self._face = self._robot.world.wait_for_observed_face(timeout=1, include_existing=True)
                    self._robot.turn_towards_face(self._face).wait_for_completed()
                except asyncio.TimeoutError:
                    self._logger.warning("Didn't find any face.")

            try:
                f = self._queue.get(timeout=self.QUEUE_TIMEOUT)
            except Empty:
                self._do_listen()
                continue

            if f == Feel.HAPPY:
                self._be_happy()
            elif f == Feel.SAD:
                self._be_sad()
            elif f == Feel.ANNOYED:
                self._be_annoyed()
            elif f == Feel.SCARED:
                self._be_scared()
            elif f == Feel.EXCITED:
                self._be_excited()
            elif f == Feel.START:
                self.play_anim("anim_speedtap_wingame_intensity03_01")
            elif f == Feel.END:
                self.do_fist_bump()

    def do_feel(self, feel: Feel):
        """Execute feeling animation."""
        self._queue.put(feel)
        if self._running_animation is not None:
            self._running_animation.abort()

    def _be_sad(self):
        """Execute sad emotion."""
        self.play_anim(
            choice(
                [
                    "anim_rtpmemorymatch_no_01",
                    "anim_speedtap_playerno_01",
                    "anim_memorymatch_failhand_02",
                    "anim_energy_cubenotfound_02",
                ]
            )
        )

    def _be_happy(self):
        """Execute happy emotion."""
        self.play_anim(
            choice(
                [
                    "anim_poked_giggle",
                    "anim_reacttoblock_happydetermined_01",
                    "anim_memorymatch_failhand_player_02",
                    "anim_pyramid_reacttocube_happy_low_01",
                    "anim_pyramid_reacttocube_happy_mid_01",
                    "anim_pyramid_reacttocube_happy_high_02",
                ]
            )
        )

    def _be_annoyed(self):
        """Execute annoyed emotion."""
        self.play_anim(
            choice(
                [
                    "anim_memorymatch_failhand_01",
                    "anim_reacttoblock_frustrated_01",
                    "anim_pyramid_reacttocube_frustrated_low_01",
                    "anim_reacttoblock_frustrated_int2_01",
                ]
            )
        )

    def _be_scared(self):
        """Execute scared emotion (Uninplemented)."""
        pass

    def _be_excited(self):
        """Execute excited emotion."""
        self.play_anim(choice(["anim_speedtap_wingame_intensity03_01", "anim_codelab_chicken_01"]))

    def _do_listen(self):
        """Do little look down/up nods."""
        play_wait = randint(0, 3)
        if play_wait == 0:
            self._logger.debug("Looking away")
            self._robot.set_head_angle(degrees(0)).wait_for_completed()
            self.play_anim(
                choice(
                    [
                        "anim_speedtap_wait_short",
                        "anim_speedtap_wait_medium",
                        "anim_speedtap_wait_medium_02",
                        "anim_speedtap_wait_medium_03",
                        "anim_speedtap_wait_long",
                    ]
                )
            )
        else:
            self._logger.debug("Looking at face")
            if self._face:
                # start turning towards the face
                self._robot.set_head_angle(self._last_head_position).wait_for_completed()
                self._robot.turn_towards_face(self._face).wait_for_completed()
                self._last_head_position = self._robot.head_angle

            time.sleep(0.5)

    def play_anim(self, anim: str):
        """Execute given animation.

        :param anim: The code for the animation to run.
        """
        try:
            self._running_animation = self._robot.play_anim(anim)
            self._running_animation.wait_for_completed()
        except Exception as e:
            self._logger.warning("Error while playing animation '{}': {}".format(anim, e))
            pass

    @event.oneshot
    def handle_fist_bump(self, event: EvtRobotMovedBish):
        """Execute action when fist bump event is triggered.

        :param event: Robot moved event.
        """
        self._logger.info(event)
        self.fist_bump_success = True

    def do_fist_bump(self):
        """Execute fist bump interaction."""
        self._logger.info("Fist bump?")
        wait_time = 10.0
        self.fist_bump_success = False

        # This event EvtRobotMovedBish is dispatched when the world receives the robot delocalized message because that
        # is what "fist bumping" tiny Cozmo does.
        self._robot.add_event_handler(EvtRobotMovedBish, self.handle_fist_bump)
        self._robot.move_lift(5)
        time.sleep(0.2)
        self._robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestOnce).wait_for_completed()

        while not self.fist_bump_success and wait_time > 0:
            time.sleep(0.5)
            wait_time -= 0.5

        if not self.fist_bump_success:
            # No fist bumo yet request again
            wait_time = 10.0
            self._logger.info("Please fist bump")
            self._robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestRetry).wait_for_completed()
            while not self.fist_bump_success and wait_time > 0:
                time.sleep(0.5)
                wait_time -= 0.5

        if self.fist_bump_success:
            self._logger.info("hehe fist bumped")
            self._robot.move_lift(-3)
            time.sleep(0.2)
            self._robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpSuccess).wait_for_completed()
        else:
            self._logger.info("Cozmo is sad, no fist bump")
            self._robot.move_lift(-3)
            time.sleep(2)
            self._robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpLeftHanging).wait_for_completed()
