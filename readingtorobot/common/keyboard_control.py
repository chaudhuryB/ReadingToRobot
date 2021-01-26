"""
    Method to trigger robot reactions using a keyword.
"""
from threading import Thread

from getkey import getkey, keys

from ..common.feeling_declaration import Feel


class EmotionController(Thread):
    """ Keyword control to trigger animations. """
    def __init__(self,
                 game):
        Thread.__init__(self)
        self.robot_proxy = game
        self.running = True

    def stop(self):
        self.running = False
        self.join()

    def run(self):
        while self.running:
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
