"""
    MiRo Robot behaviour manager.
"""

import copy
import logging
import os
import time

import numpy as np
import paho.mqtt.client as mqtt

import geometry_msgs
import rospy
import sensor_msgs
import std_msgs

import miro2 as miro
import miro2.core.pars as pars
from miro2.core.node_detect_audio_engine import DetectAudioEvent
from cv_bridge import CvBridge

# Local nodes
from .helper_classes import Input, Nodes, Output, Pub, State
from .node_animation_player import choose_animation, load_animations
from ..common.feeling_expression import Feel, FeelingReaction


class RobotManager(object):

    def __init__(self, animation_dir=None, keyboard_control=False, mqtt_ip=None, timeout=20):
        # logger
        self.logger = logging.getLogger(f'rosout.{__name__}')

        # config animations
        self.animations = load_animations(animation_dir, max_speed=10)

        # pars
        self.pars = pars.CorePars()
        self.pars.express.eyelids_droop_on_touch = 0

        # resources
        self.bridge = CvBridge()

        # Connection to command server
        self.mqtt_client = mqtt.Client("miro")
        self.mqtt_client.message_callback_add("miro/stop", self.mqtt_stop_callback)
        self.mqtt_client.message_callback_add("speech/cmd", self.mqtt_process_text)
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.connect(mqtt_ip)
        self.mqtt_client.subscribe("miro/stop", 0)
        self.mqtt_client.subscribe("speech/cmd", 0)
        self.mqtt_timeout = timeout
        self.connected_flag = False

        # emotion expression management
        self.keyboard_control = keyboard_control
        self.emotion = FeelingReaction(self)

        # init ROS
        rospy.init_node(self.pars.ros.robot_name + "_client_main", log_level=self.pars.ros.log_level)
        self.topic_base_name = "/" + self.pars.ros.robot_name + "/"

        # subs
        self.kc_m = miro.lib.kc_interf.kc_miro()
        self.kc_s = miro.lib.kc_interf.kc_miro()
        self.input = Input()
        self.state = State(self.pars)
        self.output = Output()
        self.nodes = Nodes()

        # debug
        if self.pars.dev.START_CAMS_HORIZ:
            self.logger.debug("Adjusting camera start position to horizontal")
            self.kc_m = miro.utils.kc_interf.kc_miro_cams_horiz()
            self.kc_s = miro.utils.kc_interf.kc_miro_cams_horiz()

        # state
        self.active_counter = 1
        self.active = False
        self.platform_flags = -1
        self.animal_flags = 0

        # monitor use of time (set timing0 to "None" to disable timing)
        self.timing = [[], [], []]
        self.timing0 = None  # time.time()

        # traces
        if self.pars.dev.DEBUG_WRITE_TRACES:
            with open('/tmp/kin', 'w') as file:
                file.write("")

        # ROS interfaces
        self.sub = []

        # publish priority
        self.pub_pri = [
            self.publish('core/pril', sensor_msgs.msg.Image),
            self.publish('core/prir', sensor_msgs.msg.Image),
            self.publish('core/priw', sensor_msgs.msg.Image)
            ]

        # publish control outputs
        self.pub_cos = self.publish('control/cosmetic_joints', std_msgs.msg.Float32MultiArray)
        self.pub_illum = self.publish('control/illum', std_msgs.msg.UInt32MultiArray)

        # publish core states
        self.pub_animal_state = self.publish('core/animal/state', miro.msg.animal_state)
        self.pub_sel_prio = self.publish('core/selection/priority', std_msgs.msg.Float32MultiArray)
        self.pub_sel_inhib = self.publish('core/selection/inhibition', std_msgs.msg.Float32MultiArray)

        # reference core states output messages in output array
        self.output.animal_state = self.pub_animal_state.msg
        self.output.sel_prio = self.pub_sel_prio.msg
        self.output.sel_inhib = self.pub_sel_inhib.msg

        # publish
        self.pub_flags = self.publish('control/flags', std_msgs.msg.UInt32)
        self.pub_tone = self.publish('control/tone', std_msgs.msg.UInt16MultiArray)

        # publish motor output
        self.pub_kin = self.publish('control/kinematic_joints', sensor_msgs.msg.JointState)
        self.pub_kin.msg.name = ['tilt', 'lift', 'yaw', 'pitch']
        self.pub_cmd_vel = self.publish('control/cmd_vel', geometry_msgs.msg.TwistStamped)

        # publish config
        self.pub_config = self.publish('core/config/state', std_msgs.msg.String)

        # publish audio
        self.pub_stream = self.publish('control/stream', std_msgs.msg.Int16MultiArray)

        # publish debug states JIT
        self.pub_pri_peak = None

        # instantiate nodes
        self.nodes.instantiate(self)

        # finalize parameters
        self.pars.finalize()

        # action final parameters
        if not self.pars.dev.RECONFIG_CAMERA_QUICK:
            self.state.reconfigure_cameras = True

        # and set up to reconfigure them on the fly
        self.trigger_filename = os.getenv("MIRO_DIR_STATE") + "/client_demo.reread"

        # set up to output demo state string
        self.demo_state_filename = os.getenv("MIRO_DIR_STATE") + "/client_demo.state"
        self.state_file_contents = ""

        # subscribe
        self.subscribe('sensors/package', miro.msg.sensors_package, self.callback_sensors_package)
        self.subscribe('core/voice_state', miro.msg.voice_state, self.callback_voice_state)
        self.subscribe('core/detect_motion_l', sensor_msgs.msg.Image, self.callback_movl)
        self.subscribe('core/detect_motion_r', sensor_msgs.msg.Image, self.callback_movr)
        self.subscribe('core/detect_objects_l', miro.msg.objects, self.callback_detect_objects)
        self.subscribe('core/detect_objects_r', miro.msg.objects, self.callback_detect_objects)
        self.subscribe('core/detect_audio_event', std_msgs.msg.Float32MultiArray, self.callback_audio_event)
        self.subscribe('core/config/command', std_msgs.msg.String, self.callback_config_command)
        self.subscribe('core/animal/adjust', miro.msg.animal_adjust, self.callback_animal_adjust)
        self.subscribe('core/audio_level', std_msgs.msg.Float32MultiArray, self.callback_audio_level)
        self.subscribe('sensors/stream', std_msgs.msg.UInt16MultiArray, self.callback_stream)

        # MQTT connection
        self.mqtt_client.loop_start()

        # Wait for connection
        for _ in range(self.mqtt_timeout):
            if self.connected_flag:
                break
            time.sleep(1)
        else:
            self.logger.error("MQTT connection timed out, exiting.")
            return

        # wait for connection before moving off
        self.logger.info("Waiting for connection to robot...")
        time.sleep(1)

        # set active
        self.active = True

    def subscribe(self, topic_name, data_type, callback):

        full_topic_name = self.topic_base_name + topic_name
        self.logger.debug("Subscribing to {}...".format(full_topic_name))
        self.sub.append(rospy.Subscriber(full_topic_name, data_type, callback, queue_size=1, tcp_nodelay=True))

    def publish(self, topic_name, data_type):

        return Pub(rospy.Publisher(self.topic_base_name + topic_name, data_type, queue_size=0, tcp_nodelay=True),
                   data_type)

    def do_feel(self, feeling):
        self.state.user_touch = 2.0
        if feeling == Feel.HAPPY:
            # self.state.emotion.valence = 1.0
            # self.state.emotion.arousal = 1.0
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'happy')])
            self.logger.debug("Feeling happy")
        elif feeling == Feel.SAD:
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'sad')])
            self.logger.debug("Feeling sad")
        elif feeling == Feel.ANNOYED:
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'annoyed')])
            self.logger.debug("Feeling annoyed")
        elif feeling == Feel.EXCITED:
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'excited')])
            self.logger.debug("Feeling excited")
        elif feeling == Feel.START:
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'start')])
            self.logger.debug("Starting interaction")
        elif feeling == Feel.END:
            self.nodes.animation.play_animation(self.animations[choose_animation(self.animations.keys(), 'end')])
            self.logger.debug("Finishing interaction")

    def callback_config_command(self, msg):

        # report command
        cmd = msg.data
        self.logger.debug("Callback_config_command {}".format(cmd))

        # handle command
        if len(cmd) == 0:
            pass
        elif cmd == "ping":
            pass
        elif cmd[0] == "f":
            flag = cmd[1]
            self.logger.debug("Toggle {}".format(flag))
            if flag in self.pars.demo_flags:
                self.pars.demo_flags = self.pars.demo_flags.replace(flag, '')
            else:
                self.pars.demo_flags += flag
            self.pars.action_demo_flags()
        elif cmd[0] == "p":
            q = float(cmd[1]) * 0.2
            self.pars.action.action_prob = q
            self.logger.debug("action_prob {}".format(self.pars.action.action_prob))
            self.pars.lower.interact_prob = q
            self.logger.debug("interact_prob {}".format(self.pars.lower.interact_prob))
        else:
            self.logger.warning("command not understood: {}".format(cmd))

        # return state
        self.pub_config.msg.data = "demo_flags=" + self.pars.demo_flags + \
                                   ", action_prob=" + str(self.pars.action.action_prob)
        self.pub_config.publish()

    def callback_animal_adjust(self, msg):

        self.input.animal_adjust = msg

    def callback_audio_level(self, msg):

        self.state.audio_level = np.array(msg.data)

    def callback_stream(self, msg):

        self.input.stream = msg.data

    def callback_sensors_package(self, msg):

        if not self.active:
            return

        if self.timing0 is not None:
            self.timing[0].append(time.time() - self.timing0)

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
        if state != self.state_file_contents:
            self.state_file_contents = state
            with open(self.demo_state_filename, 'wb') as file:
                file.write(state.encode())

        # publish flags only if they have changed
        platform_flags = 0
        # default flags inlcude disabled cliff reflex, disable wheels and always-enabled emotion
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_CLIFF_REFLEX
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_WHEELS
        platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_TRANSLATION

        if self.state.user_touch == 0:
            platform_flags |= miro.constants.PLATFORM_D_FLAG_DISABLE_KIN_IDLE

        if self.platform_flags != platform_flags:
            self.logger.debug("publishing flags {0:08x}".format(platform_flags))
            self.platform_flags = platform_flags
            self.pub_flags.msg.data = platform_flags
            self.pub_flags.publish()

        # publish
        self.pub_cos.msg.data = self.output.cosmetic_joints
        self.pub_cos.publish()

        # publish
        if self.pub_illum.msg.data == self.output.illum:
            # do not publish, in case users want to do their own
            pass
        else:
            self.pub_illum.msg.data = copy.copy(self.output.illum)
            self.pub_illum.publish()

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
        self.pub_animal_state.publish()
        self.pub_sel_prio.publish()
        self.pub_sel_inhib.publish()

        # publish motor output
        if self.state.animation_running:
            config = self.nodes.animation.get_config()
            self.pub_kin.msg.position = config
            self.pub_kin.publish()

        else:
            # get config & dpose from kc
            config = self.kc_m.getConfig()
            # dpose = self.kc_m.getPoseChange() * miro.constants.PLATFORM_TICK_HZ

            # handle wakefulness
            w = self.state.wakefulness
            config[1] = miro.constants.LIFT_RAD_MAX + w * (config[1] - miro.constants.LIFT_RAD_MAX)

            # publish
            self.pub_kin.msg.position = config
            self.pub_kin.publish()
            self.pub_cmd_vel.msg.twist.linear.x = 0
            self.pub_cmd_vel.msg.twist.angular.z = 0
            self.pub_cmd_vel.publish()

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
            if self.pub_pri_peak is None:
                self.pub_pri_peak = self.publish('core/debug_pri_peak', miro.msg.priority_peak)

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
                self.pub_pri_peak.pub.publish(msg)

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
            msg = self.pub_tone.msg
            msg.data = [x + 440, x, 1]
            self.pub_tone.publish()

        # tick counter
        self.state.tick += 1

        if self.timing0 is not None:
            self.timing[0].append(time.time() - self.timing0)

        # update config (from run state file)
        if os.path.isfile(self.trigger_filename):
            self.logger.debug("saw trigger file, (re)finalizing parameters")
            self.pars.finalize()
            os.remove(self.trigger_filename)

        # write traces
        if self.pars.dev.DEBUG_WRITE_TRACES:
            with open('/tmp/kin', 'a') as file:
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

    def callback_detect_objects(self, msg):

        self.state.detect_objects_for_spatial[msg.stream_index] = msg
        self.state.detect_objects_for_50Hz[msg.stream_index] = msg

    def callback_mov(self, stream_index, msg):

        if not self.active:
            return

        # store
        self.state.frame_mov[stream_index] = self.bridge.imgmsg_to_cv2(msg, "mono8")

        # tick
        updated = self.nodes.spatial.tick_camera(stream_index)

        # publish
        for i in updated:
            frame_pri = self.state.frame_pri[i]
            if frame_pri is not None:
                msg = self.bridge.cv2_to_imgmsg(frame_pri, encoding='mono8')
                self.pub_pri[i].pub.publish(msg)

    def callback_movl(self, msg):

        self.callback_mov(0, msg)

    def callback_movr(self, msg):

        self.callback_mov(1, msg)

    def callback_voice_state(self, msg):

        if not self.active:
            return

        self.input.voice_state = msg

        # DebugVoiceState
        """
        t = time.time() - 1565096267;
        x = "1 1 " + str(t) + " " + str(msg.breathing_phase) + "\n"
        with open("/tmp/voice_state", "a") as file:
            file.write(x)
        """

    def callback_audio_event(self, msg):

        q = DetectAudioEvent(msg.data)
        self.state.audio_events_for_spatial.append(q)
        self.state.audio_events_for_50Hz.append(q)

    def mqtt_stop_callback(self, cli, obj, msg):
        self.logger.info("Stop message recieved: {}".format(msg.topic))
        self.state.keep_running = False

    def mqtt_process_text(self, cli, obj, msg):
        if not self.keyboard_control:
            self.emotion.process_text(msg.payload.decode())
        else:
            self.logger.warning("Keyboard control is enabled, speech msg ignored: {} : {} : {}".format(msg.topic,
                                                                                                       msg.qos,
                                                                                                       msg.payload))

    def mqtt_on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected_flag = True
            self.logger.info("Connected to MQTT broker.")
            self.mqtt_client.publish("miro/started", 1)
        else:
            self.logger.error("Bad connection to mqtt, returned code: {}".format(rc))
            self.mqtt_client.publish("miro/started", 0)

    def loop(self):

        # main loop
        while not rospy.core.is_shutdown() and self.state.keep_running:

            # sleepy time
            time.sleep(0.1)

            # check dev stop
            if self.pars.dev.DEBUG_AUTO_STOP:
                if self.state.tick >= 400:  # set this value manually
                    self.logger.debug("DEV_DEBUG_AUTO_STOP")
                    with open("/tmp/DEV_DEBUG_AUTO_STOP", "w") as file:
                        file.write("")
                    break

            # debug
            if self.pars.dev.SHOW_LOC_EYE:
                x = miro.utils.get("LOC_EYE_L_HEAD")
                y = self.kc_m.changeFrameAbs(miro.constants.LINK_HEAD, miro.constants.LINK_WORLD, x)
                self.logger.debug("LOC_EYE_L_HEAD_WORLD {}".format(y))

        # set inactive
        self.active = False

        # timing
        if self.timing0 is not None:
            np.set_printoptions(precision=6, linewidth=1000000)
            for i in range(3):
                tt = self.timing[i]
                self.logger.debug("\n\n\n{}".format(np.array(tt)))

    def term(self):
        self.mqtt_client.loop_stop()
        # remove state file
        os.remove(self.demo_state_filename)
        # Add mqtt response saying we finished.
        self.logger.info("Sending response.")

        self.mqtt_client.publish("miro/stopped_clean", "0")
        time.sleep(5)
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
