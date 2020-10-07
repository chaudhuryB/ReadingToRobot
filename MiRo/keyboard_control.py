from getkey import getkey, keys
import threading

class feel:
    NEUTRAL = 0
    HAPPY = 1
    SAD = 2
    ANNOYED = 3
    SCARED = 4
    EXCITED = 5

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
                self.robot_proxy.do_feel(feel.HAPPY)

            elif key == keys.S:
                self.robot_proxy.do_feel(feel.SAD)

            elif key == keys.A:
                self.robot_proxy.do_feel(feel.ANNOYED)

            elif key == keys.D:
                self.robot_proxy.do_feel(feel.EXCITED)

            elif key == keys.X:
                self.robot_proxy.do_feel(feel.SCARED)

            elif key == keys.N:
                self.robot_proxy.do_feel(feel.NEUTRAL)
