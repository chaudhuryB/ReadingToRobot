from getkey import getkey, keys
import threading

from ..common.feeling_declaration import Feel


class EmotionController(threading.Thread):
    def __init__(self,
                 robot_proxy):
        threading.Thread.__init__(self)
        self.robot_proxy = robot_proxy
        self.is_running = True

    def stop(self):
        self.is_running = False
        self.join()

    def run(self):
        while self.is_running:
            key = getkey(blocking=True)
            if key == keys.W:
                self.robot_proxy.do_feel(Feel.HAPPY)

            elif key == keys.S:
                self.robot_proxy.do_feel(Feel.SAD)

            elif key == keys.A:
                self.robot_proxy.do_feel(Feel.ANNOYED)

            elif key == keys.D:
                self.robot_proxy.do_feel(Feel.EXCITED)

            elif key == keys.X:
                self.robot_proxy.do_feel(Feel.SCARED)

            elif key == keys.N:
                self.robot_proxy.do_feel(Feel.NEUTRAL)
