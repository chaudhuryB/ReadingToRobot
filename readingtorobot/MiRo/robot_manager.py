"""MiRo Robot behaviour manager."""
import copy
import logging
import os
import time
from threading import Thread

import numpy as np

import geometry_msgs
import rospy
import sensor_msgs
import std_msgs

import miro2 as miro
import miro2.core.pars as pars
from miro2.core.node_detect_audio_engine import DetectAudioEvent
from cv_bridge import CvBridge

# Local nodes
from .core import Input, Nodes, Output, Pub, State
from .node_animation_player import choose_animation, load_animations
from ..common import Feel, FeelingReaction, MQTTManager


class RobotManager(Thread):
    """
    Manager class for MiRo Robot.

    Highly inspired by the MiRo SDK's robot demo.
    """

    def __init__(self, animation_dir=None, mqtt_ip=None, timeout=20):
        """Initialize RobotManager.

        :param animation_dir: Directory containing the available robot animations.
        :type animation_dir: Optional[str]
        :param mqtt_ip: Ip of the used mqtt server (localhost by default).
        :type mqtt_ip: Optional[str]
        :param timeout: Connection timeout for mqtt client.
        :type timeout: Optional[int]
        """
        super().__init__()
        # logger
        self._logger = logging.getLogger(f"rosout.{__name__}")

        self._loop_task = None

        # config animations
        self._animations = load_animations(animation_dir, max_speed=10)

        # pars
        self.pars = pars.CorePars()
        self.pars.express.eyelids_droop_on_touch = 0

        # resources
        self._bridge = CvBridge()

        # emotion expression management
        self._emotion = FeelingReaction(self)

        # Connection to command server
        self._mqtt_client = MQTTManager("miro", self.stop, self._emotion.process_text, timeout, mqtt_ip)

        # init ROS
        rospy.init_node(self.pars.ros.robot_name + "_client_main", log_level=self.pars.ros.log_level)
        self._topic_base_name = "/" + self.pars.ros.robot_name + "/"

        # subs
        self.kc_m = miro.lib.kc_interf.kc_miro()
        self.kc_s = miro.lib.kc_interf.kc_miro()
        self.input = Input()
        self.state = State(self.pars)
        self.output = Output()
        self.nodes = Nodes()

        # debug
        if self.pars.dev.START_CAMS_HORIZ:
            self._logger.debug("Adjusting camera start position to horizontal")
            self.kc_m = miro.utils.kc_interf.kc_miro_cams_horiz()
            self.kc_s = miro.utils.kc_interf.kc_miro_cams_horiz()

        # state
        self._active_counter = 1
        self._active = False
        self._platform_flags = -1
        self._animal_flags = 0

        # monitor use of time (set timing0 to "None" to disable timing)
        self._timing = [[], [], []]
        self._timing0 = None  # time.time()

        # traces
        if self.pars.dev.DEBUG_WRITE_TRACES:
            with open("/tmp/kin", "w") as file:
                file.write("")

        # ROS interfaces
        self._sub = []

        # publish priority
        self._pub_pri = [
            self._publish("core/pril", sensor_msgs.msg.Image),
            self._publish("core/prir", sensor_msgs.msg.Image),
            self._publish("core/priw", sensor_msgs.msg.Image),
        ]

        # publish control outputs
        self._pub_cos = self._publish("control/cosmetic_joints", std_msgs.msg.Float32MultiArray)
        self._pub_illum = self._publish("control/illum", std_msgs.msg.UInt32MultiArray)

        # publish core states
        self._pub_animal_state = self._publish("core/animal/state", miro.msg.animal_state)
        self._pub_sel_prio = self._publish("core/selection/priority", std_msgs.msg.Float32MultiArray)
        self._pub_sel_inhib = self._publish("core/selection/inhibition", std_msgs.msg.Float32MultiArray)

        # reference core states output messages in output array
        self.output.animal_state = self._pub_animal_state.msg
        self.output.sel_prio = self._pub_sel_prio.msg
        self.output.sel_inhib = self._pub_sel_inhib.msg

        # publish
        self._pub_flags = self._publish("control/flags", std_msgs.msg.UInt32)
        self._pub_tone = self._publish("control/tone", std_msgs.msg.UInt16MultiArray)

        # publish motor output
        self._pub_kin = self._publish("control/kinematic_joints", sensor_msgs.msg.JointState)
        self._pub_kin.msg.name = ["tilt", "lift", "yaw", "pitch"]
        self._pub_cmd_vel = self._publish("control/cmd_vel", geometry_msgs.msg.TwistStamped)

        # publish config
        self._pub_config = self._publish("core/config/state", std_msgs.msg.String)

        # publish audio
        self._bub_stream = self._publish("control/stream", std_msgs.msg.Int16MultiArray)

        # publish debug states JIT
        self._pub_pri_peak = None

        # instantiate nodes
        self.nodes.instantiate(self)

        # finalize parameters
        self.pars.finalize()

        # action final parameters
        if not self.pars.dev.RECONFIG_CAMERA_QUICK:
            self.state.reconfigure_cameras = True

        # and set up to reconfigure them on the fly
        self._trigger_filename = os.getenv("MIRO_DIR_STATE") or "." + "/client_demo.reread"

        # set up to output demo state string
        self._demo_state_filename = os.getenv("MIRO_DIR_STATE") or "." + "/client_demo.state"
        self._state_file_contents = ""

        # subscribe
        self._subscribe("sensors/package", miro.msg.sensors_package, self._callback_sensors_package)
        self._subscribe("core/voice_state", miro.msg.voice_state, self._callback_voice_state)
        self._subscribe("core/detect_motion_l", sensor_msgs.msg.Image, self._callback_movl)
        self._subscribe("core/detect_motion_r", sensor_msgs.msg.Image, self._callback_movr)
        self._subscribe("core/detect_objects_l", miro.msg.objects, self._callback_detect_objects)
        self._subscribe("core/detect_objects_r", miro.msg.objects, self._callback_detect_objects)
        self._subscribe("core/detect_audio_event", std_msgs.msg.Float32MultiArray, self._callback_audio_event)
        self._subscribe("core/config/command", std_msgs.msg.String, self._callback_config_command)
        self._subscribe("core/animal/adjust", miro.msg.animal_adjust, self._callback_animal_adjust)
        self._subscribe("core/audio_level", std_msgs.msg.Float32MultiArray, self._callback_audio_level)
        self._subscribe("sensors/stream", std_msgs.msg.UInt16MultiArray, self._callback_stream)

        # MQTT connection
        self._mqtt_client.start()

        # wait for connection before moving off
        self._logger.info("Waiting for connection to robot...")
        time.sleep(1)

        # set active
        self._active = True

    def _subscribe(self, topic_name, data_type, callback):
        """Subscribe method to a ROS topic.

        :param topic_name: Topic name.
        :type topic_name: str
        :param data_type: ROS Message description.
        :type data_type: genpy.message.Message
        :param callback: Method to execute on new message.
        :type callback: Callable
        """
        full_topic_name = self._topic_base_name + topic_name
        self._logger.debug("Subscribing to {}...".format(full_topic_name))
        self._sub.append(rospy.Subscriber(full_topic_name, data_type, callback, queue_size=1, tcp_nodelay=True))

    def _publish(self, topic_name, data_type):
        """Create publisher for a ROS topic.

        :param topic_name: Topic name.
        :type topic_name: str
        :param data_type: ROS Message description.
        :type data_type: genpy.message.Message
        :return: Publisher object
        :rtype: Pub
        """
        return Pub(
            rospy.Publisher(self._topic_base_name + topic_name, data_type, queue_size=0, tcp_nodelay=True), data_type
        )

    def do_feel(self, feeling):
        """Execute animation for a given feeling.

        :param feeling: Feeling to execute.
        :type feeling: Feel
        """
        self.state.user_touch = 2.0
        if feeling == Feel.HAPPY:
            # self.state.emotion.valence = 1.0
            # self.state.emotion.arousal = 1.0
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "happy")])
            self._logger.debug("Feeling happy")
        elif feeling == Feel.SAD:
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "sad")])
            self._logger.debug("Feeling sad")
        elif feeling == Feel.ANNOYED:
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "annoyed")])
            self._logger.debug("Feeling annoyed")
        elif feeling == Feel.EXCITED:
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "excited")])
            self._logger.debug("Feeling excited")
        elif feeling == Feel.START:
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "start")])
            self._logger.debug("Starting interaction")
        elif feeling == Feel.END:
            self.nodes.animation.play_animation(self._animations[choose_animation(self._animations.keys(), "end")])
            self._logger.debug("Finishing interaction")

    def _callback_config_command(self, msg):
        """Update State of the robot configuration."""
        # report command
        cmd = msg.data
        self._logger.debug("Callback_config_command {}".format(cmd))

        # handle command
        if len(cmd) == 0:
            pass
        elif cmd == "ping":
            pass
        elif cmd[0] == "f":
            flag = cmd[1]
            self._logger.debug("Toggle {}".format(flag))
            if flag in self.pars.demo_flags:
                self.pars.demo_flags = self.pars.demo_flags.replace(flag, "")
            else:
                self.pars.demo_flags += flag
            self.pars.action_demo_flags()
        elif cmd[0] == "p":
            q = float(cmd[1]) * 0.2
            self.pars.action.action_prob = q
            self._logger.debug("action_prob {}".format(self.pars.action.action_prob))
            self.pars.lower.interact_prob = q
            self._logger.debug("interact_prob {}".format(self.pars.lower.interact_prob))
        else:
            self._logger.warning("command not understood: {}".format(cmd))

        # return state
        self._pub_config.msg.data = (
            "demo_flags=" + self.pars.demo_flags + ", action_prob=" + str(self.pars.action.action_prob)
        )
        self._pub_config.publish()

    def _callback_animal_adjust(self, msg):
        """Update Input on /core/animal/adjust update."""
        self.input.animal_adjust = msg

    def _callback_audio_level(self, msg):
        """Update State on /core/audio_level update."""
        self.state.audio_level = np.array(msg.data)

    def _callback_stream(self, msg):
        """Update Input on /sensors/stream update."""
        self.input.stream = msg.data

    def _callback_sensors_package(self, msg):
        """Update on sensors/package update."""
        if not self._active:
            return

        if self._timing0 is not None:
            self._timing[0].append(time.time() - self._timing0)

        # store
        self.input.sensors_package = msg

        # configure kc_s
        self.kc_s.setConfig(msg.kinematic_joints.position)

        # don't configure kc_m, it causes drift and feedback
        # effects (e.g. around movements associated with sleep)
        # self.state.motors_active = self.kc_m.setConfigIfInactive(msg.kinematic_joints.position)

        # instead, just set the active state
        self.state.motors_active = self.kc_m.isActive()

        # tick
        self.nodes.tick()

        # write demo state (first two characters is demo state version code)
        state = "01"
        if self.state.interact_enable:
            state += "I"
        else:
            state += "i"
        if state != self._state_file_contents:
            self._state_file_contents = state
            with open(self._demo_state_filename, "wb") as file:
                file.write(state.encode())

        # publish flags only if they have changed
        platform_flags = 0
        # default flags inlcude disabled cliff reflex, disable wheels and always-enabled emotion
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_CLIFF_REFLEX
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_WHEELS
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_TRANSLATION

        if self.state.user_touch == 0:
            platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_KIN_IDLE

        if self._platform_flags != platform_flags:
            self._logger.debug("publishing flags {0:08x}".format(platform_flags))
            self._platform_flags = platform_flags
            self._pub_flags.msg.data = platform_flags
            self._pub_flags.publish()

        # publish
        self._pub_cos.msg.data = self.output.cosmetic_joints
        self._pub_cos.publish()

        # publish
        if self._pub_illum.msg.data == self.output.illum:
            # do not publish, in case users want to do their own
            pass
        else:
            self._pub_illum.msg.data = copy.copy(self.output.illum)
            self._pub_illum.publish()

        # set animal state flags
        #
        # these flags are re-expressions of flags that are already present
        # in pars.flags, allowing other nodes that listen to animal_state
        # to use the same configuration as the main node (even if it changes
        # at runtime).
        self.output.animal_state.flags = 0

        # Allow vocalization when possible.
        if self.state.vocalize or (self.input.voice_state is not None and self.input.voice_state.vocalising):
            self.output.animal_state.flags |= miro.constants.ANIMAL_EXPRESS_THROUGH_VOICE
        self.output.animal_state.flags |= miro.constants.ANIMAL_EXPRESS_THROUGH_NECK
        self.output.animal_state.flags |= miro.constants.ANIMAL_EXPRESS_THROUGH_WHEELS
        self.output.animal_state.flags |= miro.constants.ANIMAL_DETECT_MOTION
        self.output.animal_state.flags |= miro.constants.ANIMAL_DETECT_BALL
        self.output.animal_state.flags |= miro.constants.ANIMAL_DETECT_FACE
        self.output.animal_state.flags |= miro.constants.ANIMAL_DETECT_SOUND
        self.output.animal_state.flags |= miro.constants.ANIMAL_DETECT_APRIL

        # publish core states
        self._pub_animal_state.publish()
        self._pub_sel_prio.publish()
        self._pub_sel_inhib.publish()

        # publish motor output
        if self.state.animation_running:
            config = self.nodes.animation.get_config()
            self._pub_kin.msg.position = config
            self._pub_kin.publish()

        else:
            # get config & dpose from kc
            config = self.kc_m.getConfig()
            # dpose = self.kc_m.getPoseChange() * miro.constants.PLATFORM_TICK_HZ

            # handle wakefulness
            w = self.state.wakefulness
            config[1] = miro.constants.LIFT_RAD_MAX + w * (config[1] - miro.constants.LIFT_RAD_MAX)

            # publish
            self._pub_kin.msg.position = config
            self._pub_kin.publish()
            self._pub_cmd_vel.msg.twist.linear.x = 0
            self._pub_cmd_vel.msg.twist.angular.z = 0
            self._pub_cmd_vel.publish()

        # clear pushes for external kc
        self.output.pushes = []

        # publish stream
        if self.output.stream:
            self.pub_stream.msg.data = self.output.stream
            self.output.stream = None
            self.pub_stream.publish()

        # debug
        if self.pars.dev.SEND_DEBUG_TOPICS:

            # publish
            if self._pub_pri_peak is None:
                self._pub_pri_peak = self._publish("core/debug_pri_peak", miro.msg.priority_peak)

            # publish
            peak = self.state.priority_peak
            if peak is not None:
                msg = miro.msg.priority_peak()
                msg.stream_index = peak.stream_index
                if peak.loc_d is not None:
                    msg.loc_d = peak.loc_d
                msg.height = peak.height
                msg.size = peak.size
                msg.azim = peak.azim
                msg.elev = peak.elev
                msg.size_norm = peak.size_norm
                msg.volume = peak.volume
                msg.range = peak.range
                msg.actioned = peak.actioned
                self._pub_pri_peak.pub.publish(msg)

        # publish
        if self.output.tone > 0:

            # output tones are debug tones
            x = max(min(self.output.tone, 255), 0)

            # over 250 are handled specially
            if x <= 250:
                self.output.tone = 0
            else:
                self.output.tone -= 1
                x = (x - 250) * 50

            # dispatch
            msg = self._pub_tone.msg
            msg.data = [x + 440, x, 1]
            self._pub_tone.publish()

        # tick counter
        self.state.tick += 1

        if self._timing0 is not None:
            self._timing[0].append(time.time() - self._timing0)

        # update config (from run state file)
        if os.path.isfile(self._trigger_filename):
            self._logger.debug("saw trigger file, (re)finalizing parameters")
            self.pars.finalize()
            os.remove(self._trigger_filename)

        # write traces
        if self.pars.dev.DEBUG_WRITE_TRACES:
            with open("/tmp/kin", "a") as file:
                sen = np.array(self.input.sensors_package.kinematic_joints.position)
                cmd = np.array(config)
                dat = np.concatenate((sen, cmd))
                dat2 = self.output.sel_inhib.data
                if len(dat2) > 0:
                    s = ""
                    for i in range(8):
                        x = dat[i]
                        s += "{0:.6f} ".format(x)
                    for i in range(len(dat2)):
                        x = dat2[i]
                        s += "{0:.6f} ".format(x)
                    s += "\n"
                    file.write(s)

        # clear inputs
        self.input.sensors_package = None
        self.state.audio_events_for_50Hz = []

    def _callback_detect_objects(self, msg):
        """Update State in core/detect_objects_l and core/detect_objects_r update."""
        self.state.detect_objects_for_spatial[msg.stream_index] = msg
        self.state.detect_objects_for_50Hz[msg.stream_index] = msg

    def _callback_mov(self, stream_index, msg):
        """Update State in core/detect_motion update."""
        if not self._active:
            return

        # store
        self.state.frame_mov[stream_index] = self._bridge.imgmsg_to_cv2(msg, "mono8")

        # tick
        updated = self.nodes.spatial.tick_camera(stream_index)

        # publish
        for i in updated:
            frame_pri = self.state.frame_pri[i]
            if frame_pri is not None:
                msg = self._bridge.cv2_to_imgmsg(frame_pri, encoding="mono8")
                self._pub_pri[i].pub.publish(msg)

    def _callback_movl(self, msg):
        """Update State in core/detect_motion_l update."""
        self._callback_mov(0, msg)

    def _callback_movr(self, msg):
        """Update State in core/detect_motion_r update."""
        self._callback_mov(1, msg)

    def _callback_voice_state(self, msg):
        """Update Input on /core/voice_state update."""
        if not self._active:
            return

        self.input.voice_state = msg

        # DebugVoiceState
        """
        t = time.time() - 1565096267;
        x = "1 1 " + str(t) + " " + str(msg.breathing_phase) + "\n"
        with open("/tmp/voice_state", "a") as file:
            file.write(x)
        """

    def _callback_audio_event(self, msg):
        """Update State in core/detect_audio_event update."""
        q = DetectAudioEvent(msg.data)
        self.state.audio_events_for_spatial.append(q)
        self.state.audio_events_for_50Hz.append(q)

    def stop(self):
        """Stop RobotManager."""
        self.state.keep_running = False
        if self.is_alive():
            self.join()

    def start(self):
        """Start RobotManager."""
        self.state.keep_running = True
        super().start()

    def run(self):
        """Execute thread task."""
        while not rospy.core.is_shutdown() and self.state.keep_running:

            # sleepy time
            time.sleep(0.1)

            # check dev stop
            if self.pars.dev.DEBUG_AUTO_STOP:
                if self.state.tick >= 400:  # set this value manually
                    self._logger.debug("DEV_DEBUG_AUTO_STOP")
                    with open("/tmp/DEV_DEBUG_AUTO_STOP", "w") as file:
                        file.write("")
                    break

            # debug
            if self.pars.dev.SHOW_LOC_EYE:
                x = miro.utils.get("LOC_EYE_L_HEAD")
                y = self.kc_m.changeFrameAbs(miro.constants.LINK_HEAD, miro.constants.LINK_WORLD, x)
                self._logger.debug("LOC_EYE_L_HEAD_WORLD {}".format(y))

        # set inactive
        self._active = False

        # timing
        if self._timing0 is not None:
            np.set_printoptions(precision=6, linewidth=1000000)
            for i in range(3):
                tt = self._timing[i]
                self._logger.debug("\n\n\n{}".format(np.array(tt)))

        # remove state file
        os.remove(self._demo_state_filename)
