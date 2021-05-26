
import datetime
import json
import numpy as np
import os
from random import choice

from miro2.core import node


class Trajectory:
    def __init__(self, angles, times, min_speed=None, max_speed=None, return_to_init=False):
        """
        Class defining the trajectory of a single joint.

        Args:
            angles (List[float]): Absolute target joint angles
            times (List[float]): Relative target times corresponding to each target position.
            min_speed (float, optional): Minimal allowed joint speed. No limit is set by default.
            max_speed (float, optional): Maximum allowed joint speed. No limit is set by default.
            return_to_init (bool, optional): If true, the trajectory will end in the same position as it starts.
                                             Defaults to False
        """

        self.angles = angles
        self.times = times
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.return_to_initial_pose = return_to_init

    def initialize(self, current_pose):
        """
        Initialization of the animation, processing the movement from and to the current position into the animation.

        Args:
            current_pose (float): Current position of the joint, in the relevant units for the joint (degrees, radians,
                                  meters..)
        """
        self.run_angles = [current_pose] + self.angles
        self.run_times = [0.0] + self.times

        # If a max limit speed is given, the current position is set as initial and final position, to avoid drastic
        # movements on the robot.
        if self.return_to_initial_pose:
            self.run_angles += [current_pose]
            self.run_times += [abs(self.run_angles[-1]-self.run_angles[-2]) / self.max_speed + self.run_times[-1]]

        self.process_anim_cmds()

    def get_target_pose(self, t):
        """
            Target angle generation.
            For now, the trajectory will keep a constant speed between positions.
            We can also assume that there won't be simultaneous animations
        Args:
            t (float): current time relative to animation start

        Returns:
            Tuple[float, bool]: Returns the target position, plus a bool indicating if the animation has ended.
        """
        for i in range(len(self.anim_vels)):
            if self.run_times[i+1] > t:
                return self.anim_vels[i] * (t - self.run_times[i]) + self.run_angles[i], False
        return self.run_angles[i+1], True

    def process_anim_cmds(self):
        self.anim_vels = []
        for i in range(1, len(self.run_angles)):
            dx = self.run_angles[i] - self.run_angles[i-1]
            dt = self.run_times[i] - self.run_times[i-1]
            try:
                target_speed = dx / dt
            except ZeroDivisionError:
                if dx == dt == 0:
                    target_speed = 0
                else:
                    raise

            if self.min_speed and target_speed < self.min_speed:
                self._update_times(dx, target_speed, self.min_speed, i)
                target_speed = self.min_speed if target_speed > 0 else -self.min_speed
            elif self.max_speed and target_speed > self.max_speed:
                self._update_times(dx, target_speed, self.max_speed, i)
                target_speed = self.max_speed if target_speed > 0 else -self.max_speed

            self.anim_vels.append(target_speed)

    def _update_times(self, dx, v, target_v, idx):
        time_diff = dx * (v - target_v) / (v * target_v)
        for t in range(idx, len(self.run_times)):
            self.run_times[t] += time_diff


class EmptyTrajectory(Trajectory):
    def __init__(self):
        Trajectory.__init__(self, [0.0], [0.0])

    def initialize(self, current_pose=0):
        self.value = current_pose
        pass

    def get_target_pose(self, t):
        return self.value, True

    def get_initial_value(self):
        return self.value

    def __bool__(self):
        return False


class EmotionTrajectory:
    def __init__(self, value):
        self.value = value
        self.run_value = 0.5

    def initialize(self, current_value):
        self.run_value = current_value

    def get_target_pose(self, t):
        return self.value, True

    def get_initial_value(self):
        return self.run_value


class NavigationCmd:
    def __init__(self, cmds, times):
        self.cmds = [0.0] + cmds
        self.times = times

    def initialize(self):
        self.run_times = [0.0] + self.times

    def get_target_pose(self, t):
        """
            Target speed generation.
        Args:
            t (float): current time relative to animation start

        Returns:
            Tuple[float, bool]: Returns the target position, plus a bool indicating if the animation has ended.
        """
        for i in range(len(self.times)):
            if self.run_times[i+1] > t:
                return self.cmds[i], False
        return self.cmds[i+1], True


class Animation:

    cosmetic_name_idx = {'tail_droop': 0, 'tail_wag': 1, 'eyel': 2, 'eyer': 3, 'earl': 4, 'earr': 5}
    kinematic_name_idx = {'tilt': 0, 'lift': 1, 'yaw': 2, 'pitch': 3}
    emotion_name_idx = {'valence': 0, 'arousal': 1}
    cmd_vel_idx = {'x_vel': 0, 'z_rot': 1}

    def __init__(self, trajectories):
        """Robot animation class, containing trajectories for the joints that will be active.

        Args:
            trajectories (Dict[str, Trajectory]): Description of joint movements
        """
        self.trajectories = trajectories
        self.ref_time = 0.0

    def initialize(self, cosmetic, kinematic, emotion):
        self.ref_time = datetime.datetime.now()
        for j in self.trajectories:
            if self.trajectories[j]['group'] == 'cosmetic':
                self.trajectories[j]['traj'].initialize(cosmetic[self.trajectories[j]['idx']])
            elif self.trajectories[j]['group'] == 'kinematic':
                self.trajectories[j]['traj'].initialize(kinematic[self.trajectories[j]['idx']])
            elif self.trajectories[j]['group'] == 'emotion':
                self.trajectories[j]['traj'].initialize(emotion[self.trajectories[j]['idx']])
            elif self.trajectories[j]['group'] == 'cmd_vel':
                self.trajectories[j]['traj'].initialize()

    def get_commands(self, kin, cos):
        kin_j, cos_j = kin, cos
        emotion = [0.0] * 2
        cmd_vel = [0.0] * 2
        dt = (datetime.datetime.now() - self.ref_time).total_seconds()
        finished = True
        for traj in self.trajectories:
            if self.trajectories[traj]['group']:
                cmd, t_ended = self.trajectories[traj]['traj'].get_target_pose(dt)
                finished &= t_ended
                if self.trajectories[traj]['group'] == 'cosmetic':
                    cos_j[self.trajectories[traj]['idx']] = cmd
                elif self.trajectories[traj]['group'] == 'kinematic':
                    kin_j[self.trajectories[traj]['idx']] = cmd
                elif self.trajectories[traj]['group'] == 'emotion':
                    emotion[self.trajectories[traj]['idx']] = cmd
                elif self.trajectories[traj]['group'] == 'cmd_vel':
                    cmd_vel[self.trajectories[traj]['idx']] = cmd
        if finished:
            return None
        else:
            return {'kinematic': kin_j, 'cosmetic': cos_j, 'emotion': emotion, 'cmd_vel': cmd_vel}

    def get_initial_emotion_level(self):
        emotion = [0.0, 0.0]
        for j in self.trajectories:
            if self.trajectories[j]['group'] == 'emotion':
                emotion[self.trajectories[j]['idx']] = self.trajectories[j]['traj'].get_initial_value()
        return emotion

    @classmethod
    def from_dict(cls, data, min_speed=None, max_speed=None):
        """
        Loads trajectories defined in json file with the format:
            {'joint_a': {
                'min_speed': 0.1,
                'max_speed': 5.0,
                'time': [t1, t2, t3,...],
                'position': [p1, p2, p3,...]},
             'joint_b': {...},
             ...
            }
        The min_speed and max_speed values are optional, and overriten by the ones specified on this call

        Args:
            data (Dict): Dict containing json data formatted as indicated.
            min_speed (float, optional): If specified, the min_speed for all joints will be set to this value.
            max_speed (float, optional): If specified, the max_speed for all joints will be set to this value.

        Returns:
            Animation: Animation object containing the target trajectories for all joints.
        """
        trajectories = {}

        def gen_traj(index_dict, group):
            for j in index_dict:
                tr = EmptyTrajectory()
                if j in data:
                    if group == 'emotion':
                        tr = EmotionTrajectory(data[j]['value'])
                    elif group == 'cmd_vel':
                        tr = NavigationCmd(data[j]['values'], data[j]['times'])
                    else:
                        mn = max(data[j]['min_speed'], min_speed) \
                            if min_speed and 'min_speed' in data[j] \
                            else data[j].get('min_speed') or min_speed
                        mx = min(data[j]['max_speed'], max_speed) \
                            if max_speed and 'max_speed' in data[j] \
                            else data[j].get('max_speed') or max_speed
                        rti = data[j].get('return_to_initial_pose', False)
                        tr = Trajectory(
                            angles=data[j]['positions'],
                            times=data[j]['times'],
                            min_speed=mn,
                            max_speed=mx,
                            return_to_init=rti)

                trajectories[j] = {
                    'traj': tr,
                    'group': group if tr else None,
                    'idx': index_dict[j]
                }

        gen_traj(cls.cosmetic_name_idx, 'cosmetic')
        gen_traj(cls.kinematic_name_idx, 'kinematic')
        gen_traj(cls.emotion_name_idx, 'emotion')
        gen_traj(cls.cmd_vel_idx, 'cmd_vel')

        return cls(trajectories=trajectories)


class NodeAnimationPlayer(node.Node):
    def __init__(self, app):
        super(NodeAnimationPlayer, self).__init__(app, 'AnimationPlayer')
        self.playing_animations = []
        self.current_animation = None
        # Kinematics target joint positions (config in the MDK)
        self.config = [0.0] * 4
        self.cmd_vel = [0.0] * 2  # normally, for miro we'll only need +/-x (fwd/bwd) and +/- z (rotation)
        self.emotion = self.output.animal_state.emotion

    def play_animation(self, anim):
        self.playing_animations.append(anim)

    def get_config(self):
        return self.config

    def get_cmd_vel(self):
        return self.cmd_vel

    def tick(self):
        """ Calculate next step in the animation."""
        if not self.current_animation:
            if self.playing_animations:
                self.current_animation = self.playing_animations.pop(0)
                self.config = self.kc_m.getConfig()
                self.current_animation.initialize(cosmetic=self.output.cosmetic_joints.tolist(),
                                                  kinematic=self.config,
                                                  emotion=(self.emotion.valence, self.emotion.arousal))
        else:
            cmds = self.current_animation.get_commands(self.config, self.output.cosmetic_joints)
            if cmds:
                self.state.animation_running = True
                self.state.vocalize = True
                self.config = cmds['kinematic']
                self.cmd_vel = cmds['cmd_vel']
                self.output.cosmetic_joints = np.array(cmds['cosmetic'])
                self.state.user_touch = 2.0
                self.state.emotion.valence = cmds['emotion'][0]
                self.state.emotion.arousal = cmds['emotion'][1]
            else:
                emotion = self.current_animation.get_initial_emotion_level()
                self.state.emotion.valence, self.state.emotion.arousal = emotion
                self.state.animation_running = False
                self.state.vocalize = False
                self.current_animation = None
                self.cmd_vel = [0.0] * 2


def get_animations_with_key(animations, key):
    return sorted([anim for anim in animations if key in anim])


def choose_animation(animations, emotion_key):
    return choice(get_animations_with_key(animations, emotion_key))


def load_animations(animation_address=None, min_speed=None, max_speed=None):
    """
    Loads the animations stored in a given address.

    Args:
        animation_address (str, optional): Path to animation folder. Defaults to <cwd>/animations.
        min_speed (float, optional): If specified, the min_speed for all joints will be set to this value.
        max_speed (float, optional): If specified, the max_speed for all joints will be set to this value.

    Returns:
        Dict[str, Animation]: Loaded animations
    """
    if not animation_address:
        animation_address = os.path.join(os.getcwd(), "animations")

    file_addr = []
    if os.path.isdir(animation_address):
        for root, _, files in os.walk(animation_address):
            if 'archived' not in root:
                for name in files:
                    if name.endswith('.json'):
                        file_addr.append(os.path.join(root, name))

    animations = {}

    for addr in file_addr:
        with open(addr, 'r') as f:
            data = json.load(f)
            animations[os.path.basename(addr)[:-5]] = Animation.from_dict(data,
                                                                          min_speed=min_speed,
                                                                          max_speed=max_speed)

    return animations
