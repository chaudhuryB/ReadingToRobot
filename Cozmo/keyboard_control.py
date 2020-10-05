from getkey import getkey, keys
import threading
from constants import (NEUTRAL,
                        HAPPY,
                        SAD,
                        ANNOYED,
                        SCARED,
                        EXCITED)

class EmotionController(threading.Thread):
    def __init__(self,
                 robot_proxy,
                 read_game):
        threading.Thread.__init__(self)
        self.robot_proxy = robot_proxy
        self.game = read_game
        self.game_on = False

    def run(self):
        while self.game_on:
            key = getkey()

            if key == keys.W:
                self.game.feel = HAPPY

            elif key == keys.S:
                self.game.feel = SAD

            elif key == keys.A:
                self.game.feel = ANNOYED

            elif key == keys.D:
                self.game.feel = EXCITED

            elif key == keys.X:
                self.game.feel = SCARED

            elif key == keys.N:
                self.game.feel = NEUTRAL
