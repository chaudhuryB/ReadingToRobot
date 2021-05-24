
import logging
import random
import time
import threading

from ..common.feeling_expression import Feel, FeelingReaction
from .nao_base import NAOBase
from .nao_expression import get_scared_movement, get_annoyed_movement, get_excited_movement, get_sad_movement, \
                            get_background_A, get_background_B, get_background_C, get_looking_down, get_arms_up, \
                            get_dab_movement
from ..common.mqtt_manager import MQTTManager


class RobotManager(NAOBase):
    """
    Class managing the movement of NAO, adding expressions when listening
    """
    def __init__(self, app, keyboard_control=False, mqtt_ip=None, timeout=20):
        """
        Initialisation of qi framework and event detection.
        """
        super(RobotManager, self).__init__(app)

        self.logger = logging.getLogger(__name__)
        self.keyboard_control = keyboard_control

        # Autonomous habilities
        self.autonomousblinking.setEnabled(True)
        self.background_thread = threading.Thread(target=self.do_background)

        # Expressions
        self.feel_lock = threading.Lock()
        self.feel_control = FeelingReaction(self)

        # Tracking
        self.tracker.registerTarget('Face', 0.3)
        self.tracker.track('Face')
        self.tracking_face = True

        # Connection to command server
        self.mqtt_client = MQTTManager('nao', self.stop, self.feel_control.process_text, timeout, mqtt_ip)

    def start(self):
        self.running = True
        self.movement.wakeUp()
        self.posture.goToPosture('Sit', 2.0)
        self.movement.setStiffnesses("Body", 1.0)
        self.background_thread.start()
        try:
            self.mqtt_client.start()
        except Exception:
            self.stop()

    def stop(self):
        self.running = False
        self.tracker.stopTracker()
        self.tracker.unregisterAllTargets()
        self.background_thread.join()
        super(RobotManager, self).stop()

    def join(self):
        self.background_thread.join()

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

            elif feeling == Feel.START:
                self.run_start_anim()

            elif feeling == Feel.END:
                self.run_end_anim()

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
                    self.do_action(*get_background_A())
                elif lot == 1:
                    self.do_action(*get_background_B())
                elif lot == 2:
                    self.do_action(*get_background_C())
                if lot >= 2:
                    self.toogle_face_book_tracking()

            time.sleep(5)
        # At the end of the loop, go back to sitting position
        self.posture.goToPosture("Sit", 0.2)

    def toogle_face_book_tracking(self):
        if self.tracking_face:
            self.last_track = self.get_back_to_target()
            self.tracker.stopTracker()
            self.do_action(*get_looking_down())
            self.tracking_face = False
        else:
            self.tracker.track('Face')
            self.do_action(*self.last_track)
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
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("enu_ono_laugh_excited_01", _async=True)
        self.do_action(*get_excited_movement(), abs=False)
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
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("frf_ono_exclamation_sad_06", _async=True)
        self.do_action(*get_sad_movement())
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

    def be_scared(self):
        """
        Execute Scared expression
        """
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("enu_ono_scared_02", _async=True)
        self.do_action(*get_scared_movement())
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

    def run_start_anim(self):
        """
        Run start animation
        """
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.ap.playSoundSetFile("enu_word_yeah", _async=True)
        self.do_action(*get_arms_up())
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True

    def run_end_anim(self):
        """
        Run start animation
        """
        if self.tracking_face:
            head_n, head_k, head_t = self.get_back_to_target()
            self.tracker.stopTracker()
        else:
            head_n, head_k, head_t = self.last_track
        self.tts.say("Hey, thank you!")
        self.do_action(*get_dab_movement())
        self.do_action(head_n, head_k, head_t)
        self.tracker.track('Face')
        self.tracking_face = True
