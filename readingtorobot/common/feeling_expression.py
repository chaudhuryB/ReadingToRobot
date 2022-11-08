"""
Available feelings and reaction management.

[Requires Python 2.7 compatibility]
"""
import logging


class Feel:
    """Enum for available emotional states."""

    NEUTRAL = 0
    HAPPY = 1
    SAD = 2
    ANNOYED = 3
    SCARED = 4
    EXCITED = 5
    START = 6
    END = 7


class FeelingReaction:
    """Class triggering the emotional responses in the robot."""

    def __init__(self, read_game):
        """Initialize feeling reaction.

        :param read_game: An object implementing the 'do_feel' method.
        :type read_game: Any
        """
        self._game = read_game
        self._logger = logging.getLogger(name=__name__)

    def process_text(self, s):
        """Check an input string and execute a feeling animation in the robot.

        :param s: The action to execute: 'happy', 'sad', 'groan', 'excited', 'scared', 'start' or 'end'
        :type s: str
        """
        self._logger.debug("\033[93mRecognized: {}\033[0m".format(s))
        try:
            if s == "happy":
                self._game.do_feel(Feel.HAPPY)
                self._logger.debug("Feeling {}".format("Happy"))
            elif s == "sad":
                self._game.do_feel(Feel.SAD)
                self._logger.debug("Feeling {}".format("Sad"))
            elif s == "groan":
                self._game.do_feel(Feel.ANNOYED)
                self._logger.debug("Feeling {}".format("Groan"))
            elif s == "excited":
                self._game.do_feel(Feel.EXCITED)
                self._logger.debug("Feeling {}".format("Excited"))
            elif s == "scared":
                self._game.do_feel(Feel.SCARED)
                self._logger.debug("Feeling {}".format("Scared"))
            elif s == "start":
                self._game.do_feel(Feel.START)
                self._logger.debug("Running interaction starting animation.")
            elif s == "end":
                self._game.do_feel(Feel.END)
                self._logger.debug("Running interaction final animation.")
        except Exception as e:
            self._logger.warning(e)
            pass
