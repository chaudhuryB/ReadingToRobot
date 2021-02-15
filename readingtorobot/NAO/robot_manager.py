
import random
import time
import threading

from ..common.speech_conn import DetachedSpeechReco
from ..common.keyboard_control import EmotionController
from ..common.feeling_declaration import Feel
from .nao_expression import get_scared_movement, get_annoyed_movement, get_excited_movement, get_sad_movement, \
                            get_background_A, get_background_B, get_background_C, get_looking_down


class RobotManager:
    """
    Class managing the movement of NAO, adding expressions when listening
    """
    def __init__(self, app, keyboard_control=False):
        """
        Initialisation of qi framework and event detection.
        """
        app.start()
        session = app.session

        # Movement
        self.movement = session.service("ALMotion")
        self.posture = session.service("ALRobotPosture")

        # Autonomous habilities
        self.autonomousblinking = session.service("ALAutonomousBlinking")
        self.autonomousblinking.setEnabled(True)
        self.background_thread = threading.Thread(target=self.do_background)

        # Expressions
        self.feel_lock = threading.Lock()
        self.ap = session.service("ALAudioPlayer")
        self.ap.loadSoundSet("Aldebaran")
        self.feel_control = EmotionController(self) if keyboard_control else DetachedSpeechReco(self)

        # Tracking
        self.tracker = session.service("ALTracker")
        self.tracker.registerTarget('Face', 0.3)
        self.tracker.track('Face')
        self.tracking_face = True

    def start(self):
        self.running = True
        self.movement.wakeUp()
        self.posture.goToPosture('Sit', 2.0)
        self.feel_control.start()
        self.movement.setStiffnesses("Body", 1.0)
        self.background_thread.start()

    def stop(self):
        self.running = False
        self.tracker.stopTracker()
        self.tracker.unregisterAllTargets()
        self.background_thread.join()
        self.movement.rest()
        self.feel_control.stop()

    def do_feel(self, feeling=Feel.NEUTRAL):
        """
        Calls robot movement based on current feel
        """
        with self.feel_lock:
            if feeling == Feel.ANNOYED:
                self.be_annoyed()

            elif feeling == Feel.EXCITED:
                self.be_excited()

            elif feeling == Feel.HAPPY:
                self.be_happy()

            elif feeling == Feel.SAD:
                self.be_sad()

            elif feeling == Feel.SCARED:
                self.be_scared()

    def do_action(self, names, keys, times, abs=True):
        """
        Executes a robot movement given a set of joint names, angles and times

        Args:
            names ([string]):   Names of joints to move
            keys ([[float]]):   Each entry contains a list object containing the target positions of
                                each joint
            times ([[float]]):  Each entry contains a list object containing the target times for each
                                joint position
        """
        try:
            self.movement.angleInterpolation(names, keys, times, abs)
        except BaseException:
            raise

    def get_back_to_target(self, ret_time=0.7):
        head_pitch = self.movement.getAngles('HeadPitch', True)
        head_yaw = self.movement.getAngles('HeadYaw', True)
        names = ['HeadPitch', 'HeadYaw']
        keys = [head_pitch, head_yaw]
        times = [[ret_time], [ret_time]]
        return names, keys, times

    def get_back_to_pos(self, names, ret_time=0.7):
        keys = list()
        times = list()
        out_names = list()
        for x in names:
            if x != 'HeadPitch' and x != 'HeadYaw':
                out_names.append(x)
                keys.append(self.movement.getAngles(x, True))
                times.append([ret_time])

        return out_names, keys, times

    def do_background(self):
        """
        Moves the robot randomly to different positions
        """
        while self.running:
            with self.feel_lock:
                lot = random.randint(0, 4)
                if lot == 0:
                    names, keys, times = get_background_A()
                    self.do_action(names, keys, times)
                elif lot == 1:
                    names, keys, times = get_background_B()
                    self.do_action(names, keys, times)
                elif lot == 2:
                    names, keys, times = get_background_C()
                    self.do_action(names, keys, times)
                if lot >= 2:
                    self.toogle_face_book_tracking()

            time.sleep(5)
        # At the end of the loop, go back to sitting position
        self.posture.goToPosture("Sit", 0.2)

    def toogle_face_book_tracking(self):
        if self.tracking_face:
            names, keys, times = get_looking_down()
            self.last_track = self.get_back_to_target()
            self.tracker.stopTracker()
            self.do_action(names, keys, times)
            self.tracking_face = False
        else:
            self.tracker.track('Face')
            self.do_action(self.last_track[0], self.last_track[1], self.last_track[2])
            self.tracking_face = True

    def be_annoyed(self):
        """
        Execute Annoyed expression
        """
        names, keys, times = get_annoyed_movement()
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target(ret_time=0.8)
            body_n, body_k, body_t = self.get_back_to_pos(names=names, ret_time=0.8)
            body_n += head_n
            body_k += head_k
            body_t += head_t
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
            body_n, body_k, body_t = self.get_back_to_pos(names=names, ret_time=0.8)
            body_n += head_n
            body_k += head_k
            body_t += head_t

        self.ap.playSoundSetFile("enu_ono_exclamation_disapointed_05", _async=True)
        self.do_action(names, keys, times)
        self.do_action(body_n, body_k, body_t)

        self.tracker.track('Face')
        self.tracking_face = True

    def be_excited(self):
        """
        Execute Excited expression
        """
        names, keys, times = get_excited_movement()
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("enu_ono_laugh_excited_01", _async=True)
        self.do_action(names, keys, times, False)
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

    def be_happy(self):
        """
        Execute Happy expression
        """
        self.be_excited()

    def be_sad(self):
        """
        Execute Sad expression
        """
        names, keys, times = get_sad_movement()
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("frf_ono_exclamation_sad_06", _async=True)
        self.do_action(names, keys, times)
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

    def be_scared(self):
        """
        Execute Scared expression
        """
        names, keys, times = get_scared_movement()
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("enu_ono_scared_02", _async=True)
        self.do_action(names, keys, times)
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

