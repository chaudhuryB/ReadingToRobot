"""Base management class for NAO."""


class NAOBase(object):
    """Basic robot connection.

    It connects to the robot and provies access to the naoqi API.

    :param movement: 'ALMotion' service interface.
    :param posture: 'ALRobotPosture' service interface.
    :param autonomousblinking: 'ALAutonomousBlinking' service interface.
    :param ap: 'ALAudioPlayer' service interface.
    :param tts: 'ALTextToSpeech' service interface.
    :param tracker: 'ALTracker' service interface.
    """

    def __init__(self, app):
        """Initialise qi framework and event detection.

        :param app: Naoqi application.
        :type app: qi.Application
        """
        app.start()
        session = app.session

        # Movement
        self.movement = session.service("ALMotion")
        self.posture = session.service("ALRobotPosture")

        # Autonomous habilities
        self.autonomousblinking = session.service("ALAutonomousBlinking")

        # Expressions
        self.ap = session.service("ALAudioPlayer")
        try:
            self.ap.loadSoundSet("Aldebaran")
        except AttributeError:
            pass

        # Text to speech
        self.tts = session.service("ALTextToSpeech")

        # Tracking
        self.tracker = session.service("ALTracker")

    def stop(self):
        """Stop the robot."""
        self.movement.rest()

    def do_action(self, names, keys, times, abs=True):
        """Execute a robot movement given a set of joint names, angles and times.

        :param names: Names of joints to move.
        :type names: List[string]
        :param keys: Each entry contains a list object containing the target position of each joint.
        :type keys: List[List[float]]
        :param times: Each entry contains a list object containing the target times for each joint position.
        :type times: List[List[float]]
        :param abs: True for absolute angles, false for relative to last position.
        :type abs: bool
        """
        try:
            self.movement.angleInterpolation(names, keys, times, abs)
        except BaseException:
            raise
