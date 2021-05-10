

class NAOBase(object):
    """
    Basic robot configuration.
    """
    def __init__(self, app):
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
        self.movement.rest()

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
