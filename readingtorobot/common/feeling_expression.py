"""
    Available feelings and reaction management.

    [Requires Python 2.7 compatibility]

"""


class Feel:
    """ Enum for available emotional states. """
    NEUTRAL = 0
    HAPPY = 1
    SAD = 2
    ANNOYED = 3
    SCARED = 4
    EXCITED = 5
    START = 6
    END = 7


class FeelingReaction:
    """ Class triggering the emotional responses in the robot. """
    def __init__(self, read_game):
        self.game = read_game

    def process_text(self, s):
        """ Check an input string and execute a feeling animation in the robot. """
        self.logger.debug("\033[93mRecognized: {}\033[0m".format(s))
        try:
            if s == "happy":
                self.game.do_feel(Feel.HAPPY)
                self.logger.debug("Feeling {}".format("Happy"))
            elif s == "sad":
                self.game.do_feel(Feel.SAD)
                self.logger.debug("Feeling {}".format("Sad"))
            elif s == "groan":
                self.game.do_feel(Feel.ANNOYED)
                self.logger.debug("Feeling {}".format("Groan"))
            elif s == "excited":
                self.game.do_feel(Feel.EXCITED)
                self.logger.debug("Feeling {}".format("Excited"))
            elif s == "scared":
                self.game.do_feel(Feel.SCARED)
                self.logger.debug("Feeling {}".format("Scared"))
            elif s == "start":
                self.game.do_feel(Feel.START)
                self.logger.debug("Running interaction starting animation.")
            elif s == "end":
                self.game.do_feel(Feel.END)
                self.logger.debug("Running interaction final animation.")
        except Exception as e:
            self.logger.warning(e)
            pass
