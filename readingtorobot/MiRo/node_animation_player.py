"""Methods executing defined actions/movements in MiRo."""
import datetime
import json
import numpy as np
import os
from random import choice

from miro2.core import node


class Trajectory:
    """Defines the trajectory of a single joint."""

    def __init__(self, angles, times, min_speed=None, max_speed=None, return_to_init=False):
        """Class defining the trajectory of a single joint.

        :param angles: Absolute target joint angles.
        :type angles: List[float]
        :param times: Relative target times corresponding to each target position.
        :type times: List[float]
        :param min_speed: Minimal allowed joint speed. No limit is set by default.
        :type min_speed: Optional[float]
        :param max_speed: Maximum allowed joint speed. No limit is set by default.
        :type max_speed: Optional[float]
        :param return_to_init: If true, the trajectory will end in the same position as it starts.
        :type return_to_init: bool
        """
        self._angles = angles
        self._times = times
        self._min_speed = min_speed
        self._max_speed = max_speed
        self._return_to_initial_pose = return_to_init

    def initialize(self, current_pose):
        """Initialize the animation, processing the movement from and to the current position into the animation.

        :param current_pose: Current position of the joint, in the relevant units for the joint.
        :type current_pose: float
        """
        self._run_angles = [current_pose] + self._angles
        self._run_times = [0.0] + self._times

        # If a max limit speed is given, the current position is set as initial and final position, to avoid drastic
        # movements on the robot.
        if self._return_to_initial_pose:
            self._run_angles += [current_pose]
            self._run_times += [
                abs(self._run_angles[-1] - self._run_angles[-2]) / self._max_speed + self._run_times[-1]
            ]

        self._process_anim_cmds()

    def get_target_pose(self, t):
        """Generate target angles.

        For now, the trajectory will keep a constant speed between positions.
        We can also assume that there won't be simultaneous animations
        :param t: Current time relative to animation start.
        :type t: float
        :return: Target position plus a boolean indicating if the animation has ended.
        :rtype: Tuple[float, bool]
        """
        i = 0
        for _ in range(len(self._anim_vels)):
            if self._run_times[i + 1] > t:
                return self._anim_vels[i] * (t - self._run_times[i]) + self._run_angles[i], False
            i += 1
        return self._run_angles[i + 1], True

    def _process_anim_cmds(self):
        """Read animation commands and generate movement data."""
        self._anim_vels = []
        for i in range(1, len(self._run_angles)):
            dx = self._run_angles[i] - self._run_angles[i - 1]
            dt = self._run_times[i] - self._run_times[i - 1]
            try:
                target_speed = dx / dt
            except ZeroDivisionError:
                if dx == dt == 0:
                    target_speed = 0
                else:
                    raise

            if self._min_speed and target_speed < self._min_speed:
                self._update_times(dx, target_speed, self._min_speed, i)
                target_speed = self._min_speed if target_speed > 0 else -self._min_speed
            elif self._max_speed and target_speed > self._max_speed:
                self._update_times(dx, target_speed, self._max_speed, i)
                target_speed = self._max_speed if target_speed > 0 else -self._max_speed

            self._anim_vels.append(target_speed)

    def _update_times(self, dx, v, target_v, idx):
        time_diff = dx * (v - target_v) / (v * target_v)
        for t in range(idx, len(self._run_times)):
            self._run_times[t] += time_diff


class EmptyTrajectory(Trajectory):
    """Keep static position.

    Used to keep the position of a joint or other element.
    """

    def __init__(self):
        """Initialize trajectory."""
        Trajectory.__init__(self, [0.0], [0.0])

    def initialize(self, current_pose=0):
        """Initialize the trajectory to the position value that will be used.

        :param current_pose: Current joint position.
        :type current_pose: float
        """
        self._value = current_pose
        pass

    def get_target_pose(self, t):
        """Return the target position for this trajectory at time 't'.

        :param t: Current time relative to animation start.
        :type t: float
        :return: Returns the target position, plus a bool indicating if the animation has ended.
        :rtype: Tuple[float, bool]
        """
        del t
        return self._value, True

    def get_initial_value(self):
        """Return the initial trajectory value.

        :return: Initial position.
        :rtype: float
        """
        return self._value

    def __bool__(self):
        """Evaluate always to False."""
        return False


class EmotionTrajectory:
    """Trajectory of emotion values (sleepyness, happiness, etc)."""

    def __init__(self, value):
        """Trajectory of emotion values.

        :param value: Default value for this emotion.
        :type value: float
        """
        self._value = value
        self._run_value = 0.5

    def initialize(self, current_value):
        """Initialize the trajectory to the position value that will be used.

        :param current_pose: Current joint position.
        :type current_pose: float
        """
        self._run_value = current_value

    def get_target_pose(self, t):
        """Return the target position for this trajectory at time 't'.

        :param t: Current time relative to animation start.
        :type t: float
        :return: Returns the target position, plus a bool indicating if the animation has ended.
        :rtype: Tuple[float, bool]
        """
        del t
        return self._value, True

    def get_initial_value(self):
        """Return the initial trajectory value.

        :return: Initial position.
        :rtype: float
        """
        return self._run_value


class NavigationCmd:
    """Joint trajectory command."""

    def __init__(self, cmds, times):
        """Joint trajectory command.

        :param cmds: List of positions to move the joint to.
        :type cmds: List[float]
        :param times: List of times corresponding to the time requested for each joint position.
        :type times: List[float]
        """
        self._cmds = [0.0] + cmds
        self._times = times

    def initialize(self):
        """Initialize the trajectory to the position value that will be used."""
        self._run_times = [0.0] + self._times

    def get_target_pose(self, t):
        """Target speed generation.

        :param t: Current time relative to animation start.
        :type t: float
        :return: Returns the target position, plus a bool indicating if the animation has ended.
        :rtype: Tuple[float, bool]
        """
        for i in range(len(self._times)):
            if self._run_times[i + 1] > t:
                return self._cmds[i], False
        return self._cmds[i + 1], True


class Animation:
    """Full animation of a movement."""

    cosmetic_name_idx = {"tail_droop": 0, "tail_wag": 1, "eyel": 2, "eyer": 3, "earl": 4, "earr": 5}
    kinematic_name_idx = {"tilt": 0, "lift": 1, "yaw": 2, "pitch": 3}
    emotion_name_idx = {"valence": 0, "arousal": 1}
    cmd_vel_idx = {"x_vel": 0, "z_rot": 1}

    def __init__(self, trajectories):
        """Robot animation class, containing trajectories for the joints that will be active.

        Args:
            trajectories (Dict[str, Trajectory]): Description of joint movements
        """
        self._trajectories = trajectories
        self._ref_time = datetime.datetime.now()

    def initialize(self, cosmetic, kinematic, emotion):
        """Initialize animation to current cosmetic, emotion and kinematic values.

        :param cosmetic: Cosmetic joint values.
        :type cosmetic: List[float]
        :param kinematic: Kinematic joint positions.
        :type kinematic: List[float]
        :param emotion: Emotion levels (valence and arousal).
        :type emotion: Tuple[float, float]
        """
        self._ref_time = datetime.datetime.now()
        for j in self._trajectories:
            if self._trajectories[j]["group"] == "cosmetic":
                self._trajectories[j]["traj"].initialize(cosmetic[self._trajectories[j]["idx"]])
            elif self._trajectories[j]["group"] == "kinematic":
                self._trajectories[j]["traj"].initialize(kinematic[self._trajectories[j]["idx"]])
            elif self._trajectories[j]["group"] == "emotion":
                self._trajectories[j]["traj"].initialize(emotion[self._trajectories[j]["idx"]])
            elif self._trajectories[j]["group"] == "cmd_vel":
                self._trajectories[j]["traj"].initialize()

    def get_commands(self, kin, cos):
        """Return the kinematic, cosmetic, emotional and wheel speed values for this trajectory.

        :param kin: Current kinematic values.
        :type kin: List[float]
        :param cos: Current cosmetic joint values.
        :type cos: List[float]
        :return: Updated values for next tick.
        :rtype: Optional[Dict]
        """
        kin_j, cos_j = kin, cos
        emotion = [0.0] * 2
        cmd_vel = [0.0] * 2
        dt = (datetime.datetime.now() - self._ref_time).total_seconds()
        finished = True
        for traj in self._trajectories:
            if self._trajectories[traj]["group"]:
                cmd, t_ended = self._trajectories[traj]["traj"].get_target_pose(dt)
                finished &= t_ended
                if self._trajectories[traj]["group"] == "cosmetic":
                    cos_j[self._trajectories[traj]["idx"]] = cmd
                elif self._trajectories[traj]["group"] == "kinematic":
                    kin_j[self._trajectories[traj]["idx"]] = cmd
                elif self._trajectories[traj]["group"] == "emotion":
                    emotion[self._trajectories[traj]["idx"]] = cmd
                elif self._trajectories[traj]["group"] == "cmd_vel":
                    cmd_vel[self._trajectories[traj]["idx"]] = cmd
        if finished:
            return None
        else:
            return {"kinematic": kin_j, "cosmetic": cos_j, "emotion": emotion, "cmd_vel": cmd_vel}

    def get_initial_emotion_level(self):
        """Return the initial values for emotion valence and arousal.

        :return: Initial emotion level.
        :rtype: Tuple[float, float]
        """
        emotion = [0.0, 0.0]
        for j in self._trajectories:
            if self._trajectories[j]["group"] == "emotion":
                emotion[self._trajectories[j]["idx"]] = self._trajectories[j]["traj"].get_initial_value()
        return emotion

    @classmethod
    def from_dict(cls, data, min_speed=None, max_speed=None):
        """Load trajectories defined in JSON format.

        The JSON structure has the format the format:
            {'joint_a': {
                'min_speed': 0.1,
                'max_speed': 5.0,
                'time': [t1, t2, t3,...],
                'position': [p1, p2, p3,...]},
             'joint_b': {...},
             ...
            }
        The min_speed and max_speed values are optional, and overriten by the ones specified on this call

        :param data: Dict containing json data formatted as indicated.
        :type data: Dict
        :param min_speed: If specified, the min_speed for all joints will be set to this value.
        :type min_speed: Optional[float]
        :param max_speed: If specified, the max_speed for all joints will be set to this value.
        :type max_speed: Optional[float]
        :return: Animation object containing the target trajectories for all joints.
        :rtype: Animation
        """
        trajectories = {}

        def gen_traj(index_dict, group):
            for j in index_dict:
                tr = EmptyTrajectory()
                if j in data:
                    if group == "emotion":
                        tr = EmotionTrajectory(data[j]["value"])
                    elif group == "cmd_vel":
                        tr = NavigationCmd(data[j]["values"], data[j]["times"])
                    else:
                        mn = (
                            max(data[j]["min_speed"], min_speed)
                            if min_speed and "min_speed" in data[j]
                            else data[j].get("min_speed") or min_speed
                        )
                        mx = (
                            min(data[j]["max_speed"], max_speed)
                            if max_speed and "max_speed" in data[j]
                            else data[j].get("max_speed") or max_speed
                        )
                        rti = data[j].get("return_to_initial_pose", False)
                        tr = Trajectory(
                            angles=data[j]["positions"],
                            times=data[j]["times"],
                            min_speed=mn,
                            max_speed=mx,
                            return_to_init=rti,
                        )

                trajectories[j] = {"traj": tr, "group": group if tr else None, "idx": index_dict[j]}

        gen_traj(cls.cosmetic_name_idx, "cosmetic")
        gen_traj(cls.kinematic_name_idx, "kinematic")
        gen_traj(cls.emotion_name_idx, "emotion")
        gen_traj(cls.cmd_vel_idx, "cmd_vel")

        return cls(trajectories=trajectories)


class NodeAnimationPlayer(node.Node):
    """ROS Node managing the animations of the robot."""

    def __init__(self, app):
        """Initialize the animation player.

        :param app: The current app running.
        :type app: RobotManager
        """
        super(NodeAnimationPlayer, self).__init__(app, "AnimationPlayer")
        self._playing_animations = []
        self._current_animation = None
        # Kinematics target joint positions (config in the MDK)
        self._config = [0.0] * 4
        self._cmd_vel = [0.0] * 2  # normally, for miro we'll only need +/-x (fwd/bwd) and +/- z (rotation)
        self._emotion = self.output.animal_state.emotion

    def play_animation(self, anim):
        """Execute the required animation.

        :param anim: The specified animation.
        :type anim: str
        """
        self._playing_animations.append(anim)

    def get_config(self):
        """Return the current robot kinematic joints.

        :return: Robot joint positions.
        :rtype: List[float]
        """
        return self._config

    def get_cmd_vel(self):
        """Return the current cmd_vel of the robot.

        :return: The velocity values for the left and right wheels of the robot.
        :rtype: List[float]
        """
        return self._cmd_vel

    def tick(self):
        """Calculate next step in the animation."""
        if not self._current_animation:
            if self._playing_animations:
                self._current_animation = self._playing_animations.pop(0)
                self._config = self.kc_m.getConfig()
                self._current_animation.initialize(
                    cosmetic=self.output.cosmetic_joints.tolist(),
                    kinematic=self._config,
                    emotion=(self._emotion.valence, self._emotion.arousal),
                )
        else:
            cmds = self._current_animation.get_commands(self._config, self.output.cosmetic_joints)
            if cmds:
                self.state.animation_running = True
                self.state.vocalize = True
                self._config = cmds["kinematic"]
                self._cmd_vel = cmds["cmd_vel"]
                self.output.cosmetic_joints = np.array(cmds["cosmetic"])
                self.state.user_touch = 2.0
                self.state.emotion.valence = cmds["emotion"][0]
                self.state.emotion.arousal = cmds["emotion"][1]
            else:
                emotion = self._current_animation.get_initial_emotion_level()
                self.state.emotion.valence, self.state.emotion.arousal = emotion
                self.state.animation_running = False
                self.state.vocalize = False
                self._current_animation = None
                self._cmd_vel = [0.0] * 2


def get_animations_with_key(animations, key):
    """Return all animations with a specific emotion key.

    :param animations: List of all available animations.
    :type animations: List[str]
    :param key: The emotion key required.
    :type key: str
    :return: The requested animations.
    :rtype: List[str]
    """
    return sorted([anim for anim in animations if key in anim])


def choose_animation(animations, emotion_key):
    """Choose a random animation from a list.

    :param animations: Complete list available animations
    :type animations: List[str]
    :param emotion_key: Specific emotion to choose from.
    :type emotion_key: str
    :return: The selected animation
    :rtype: str
    """
    return choice(get_animations_with_key(animations, emotion_key))


def load_animations(animation_address=None, min_speed=None, max_speed=None):
    """Load the animations stored in a given address.

    :param animation_address: Path to animation folder. Defaults to <cwd>/animations.
    :type animation_address: Optional[str]
    :param min_speed: If specified, the min_speed for all joints will be set to this value.
    :type min_speed: Optional[float]
    :param max_speed: If specified, the max_speed for all joints will be set to this value.
    :type max_speed: Optional[float]
    :return: Loaded animations.
    :rtype: Dict[str, Animation]
    """
    if not animation_address:
        animation_address = os.path.join(os.getcwd(), "animations")

    file_addr = []
    if os.path.isdir(animation_address):
        for root, _, files in os.walk(animation_address):
            if "archived" not in root:
                for name in files:
                    if name.endswith(".json"):
                        file_addr.append(os.path.join(root, name))

    animations = {}

    for addr in file_addr:
        with open(addr, "r") as f:
            data = json.load(f)
            animations[os.path.basename(addr)[:-5]] = Animation.from_dict(
                data, min_speed=min_speed, max_speed=max_speed
            )

    return animations
