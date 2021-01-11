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
        self.is_running = False
        self.join()

    def run(self):
        while self.is_running:
            key = getkey(blocking=True)
            if key == keys.W:
                self.game.do_feel(Feel.HAPPY)

            elif key == keys.S:
                self.game.do_feel(Feel.SAD)

            elif key == keys.A:
                self.game.do_feel(Feel.ANNOYED)

            elif key == keys.D:
                self.game.do_feel(Feel.EXCITED)

            elif key == keys.X:
                self.game.do_feel(Feel.SCARED)

            elif key == keys.N:
                self.game.do_feel(Feel.NEUTRAL)
