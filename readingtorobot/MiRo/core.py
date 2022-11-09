"""Auxiliary classes for managing ROS interactions."""
import numpy as np

from miro2.core.node_lower import NodeLower
from miro2.core.node_affect import NodeAffect
from miro2.core.node_express import NodeExpress
from miro2.core.node_action import NodeAction
from miro2.core.node_loop import NodeLoop
from miro2.core.node_spatial import NodeSpatial

from .node_animation_player import NodeAnimationPlayer


class Pub:
    """Manage a ROS Publisher.

    :param pub: ROS Publisher.
    :param msg: Message to be sent.
    """

    def __init__(self, pub, data_type):
        """Initialize Pub.

        :param pub: Topic name.
        :type pub: str
        :param data_type: ROS Message description.
        :type data_type: genpy.message.Message
        """
        # if data_type is not None, instantiate a message
        if data_type is not None:
            msg = data_type()
        else:
            msg = None

        self.pub = pub
        self.msg = msg

    def publish(self):
        """Execute publication of currently stored message."""
        # if a msg was passed
        self.pub.publish(self.msg)


class Input:
    """Manage input date.

    :param sensors_package: Sensor data.
    :param stream: Sensor data stream.
    :param voice_state: Animal voice module state.
    :param mics: Microphone data.
    :param animal_adjust: Animal behaviour state.
    """

    def __init__(self):
        """Initialize Input."""
        # instantiate
        self.sensors_package = None
        self.stream = None
        self.voice_state = None
        self.mics = None
        self.animal_adjust = None


class State:
    """Compilation of data about the robot state."""

    def __init__(self, pars):
        """Initialize state struct.

        :param pars: Unused.
        """
        del pars
        # shared resources
        self.camera_model_full = None
        self.camera_model_mini = None

        self.animation_running = False
        self.vocalize = False

        # system
        self.tick = 0
        self.keep_running = True

        # 50Hz
        self.motors_active = False
        self.user_touch = 0.0
        self.light_mean = 0.0
        self.pet = 0.0
        self.stroke = 0.0
        self.jerk_head = 0.0
        self.jerk_body = 0.0
        self.emotion = None
        self.wakefulness = 0.0
        self.fovea_speed = 0.0
        self.halting = False
        self.action_target_valence = None
        self.action_target_arousal = None
        self.interact_enable = True

        # loop feedback
        self.in_blink = 0.0
        self.in_cos_body = 0.0
        self.in_cos_head = 0.0
        self.in_motion = 0.0
        self.in_vocalising = 0.0
        self.in_making_noise = 0.0

        # cameras
        self.frame_bgr_full = [None, None]  # full size decoded frame
        self.frame_gry_full = [None, None]  # frame_bgr_full, but greyscaled
        self.frame_bgr = [None, None]  # frame_bgr_full, but reduced in size
        self.frame_gry = [None, None]  # frame_bgr, but greyscaled
        self.frame_mov = [None, None]
        self.frame_bal = [None, None]
        self.frame_pri = [None, None, None]

        # stimulus source information
        self.priority_peak = None

        # mics
        self.audio_events_for_spatial = []
        self.audio_events_for_50Hz = []
        self.audio_level = None

        # detected objects
        self.detect_objects_for_spatial = [None, None]
        self.detect_objects_for_50Hz = [None, None]

        # internal
        self.reconfigure_cameras = False
        self.reconfigured_cameras = False


class Output:
    """Data to be sent to the robot.

    :param cosmetic_joints: Cosmetic joint positions (tail, ears).
    :param illum: Lights.
    :param affect: Affectivity level.
    :param pushes: ??
    :param tone: ??
    :param stream: ??
    """

    def __init__(self):
        """Initialize Output."""
        # instantiate
        self.cosmetic_joints = np.array([0, 0.5, 0.5, 0.5, 0.2, 0])
        self.illum = [0] * 6
        self.affect = None
        self.pushes = []
        self.tone = 0
        self.stream = None


class Nodes:
    """ROS Nodes used for controlling MiRo."""

    def instantiate(self, app):
        """Start nodes for MiRo app."""
        self.lower = NodeLower(app)
        self.affect = NodeAffect(app)
        self.express = NodeExpress(app)
        self.action = NodeAction(app)
        self.loop = NodeLoop(app)
        self.spatial = NodeSpatial(app)
        self.animation = NodeAnimationPlayer(app)

    def tick(self):
        """Run update for all node."""
        self.lower.tick()
        self.affect.tick()
        self.express.tick()
        self.action.tick()
        self.loop.tick()
        self.animation.tick()
