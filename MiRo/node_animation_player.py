
import datetime
from miro2.core import node
from miro2.utils import kc


class Trajectory:
    def __init__(self, angles, times, min_speed=None, max_speed=None):
        """
        Class defining the trajectory of a single joint.

        Args:
            angles (List[float]): Absolute target joint angles
            times (List[float]): Relative target times corresponding to each target position.
            min_speed (float, optional): Minimal allowed joint speed. No limit is set by default.
            max_speed (float, optional): Maximum allowed joint speed. No limit is set by default.
        """

        self.angles = angles
        self.times = times
        self.min_speed = min_speed
        self.max_speed = max_speed

    def initialize(self, current_pose):
        self.run_angles = [current_pose] + self.angles
        self.run_times = [0.0] + self.times
        self.process_anim_cmds()

    def get_cmd_vel(self, t):
        """
            Target angle generation.
            For now, the trajectory will keep a constant speed between positions.
            We can also assume that there won't be simultaneous animations
        Args:
            t (float): current time relative to animation start

        Returns:
            Tuple[float, bool]: Returns the target position, plus a bool indicating if the animation has ended.
        """
        for i, speed in enumerate(self.anim_cmds):
            if self.times[i+1] > t:
                return t * speed, False
        return t * speed, True

    def process_anim_cmds(self):
        cmds = []
        for i in xrange(1, len(self.run_angles)):
            dx = self.run_angles[i] - self.run_angles[i-1]
            dt = self.run_times[i] - self.run_times[i-1]
            target_speed = (dx) / ()

            if self.min_speed and target_speed < self.min_speed:
                target_speed = self.min_speed
                self._update_times(dx, dt, self.min_speed, i)
            elif self.max_speed and self.target_speed > self.max_speed:
                target_speed = self.max_speed
                self._update_times(dx, dt, self.max_speed, i)

            cmds.append(target_speed)
        return cmds

    def _update_times(self, dx, dt, target, idx):
        time_diff = (dx) / target + dt
        for t in xrange(idx, len(self.run_angles)):
            self.run_times[idx] += time_diff


class EmptyTrajectory(Trajectory):
    def __init__(self):
        super(EmptyTrajectory, self).__init__([0.0], [0.0])

    def initialize(self, current_pose):
        self.run_angles = current_pose
        pass

    def get_cmd_vel(self):
        return self.run_angles, True


class Animation:
    def __init__(self, trajectories):
        """Robot animation class, containing trajectories for the joints that will be active.

        Args:
            trajectories (Dict[str, Trajectory]): Description of joint movements
        """
        self.trajectories = trajectories
        self.ref_time = 0.0

        self.cosmetic_name_idx = {'tail_droop': 0, 'tail_wag': 1, 'eyel': 2, 'eyer': 3, 'earl': 4, 'earr': 5}
        self.kinematic_name_idx = {'tilt': 0, 'lift': 1, 'yaw': 2, 'pitch': 3}

        for name in self.cosmetic_name_idx:
            if name not in self.trajectories:
                self.trajectories[name] = EmptyTrajectory()
        for name in self.kinematic_name_idx:
            if name not in self.trajectories:
                self.trajectories[name] = EmptyTrajectory()

    def initialize(self, cosmetic, kinematic):
        self.ref_time = datetime.datetime.now()
        for name in self.cosmetic_name_idx:
            self.trajectories[name].initialize(cosmetic[self.cosmetic_name_idx[name]])
        for name in self.kinematic_name_idx:
            self.trajectories[name].initialize(cosmetic[self.kinematic_name_idx[name]])

    def get_commands(self):
        kin_j, cos_j = [0.0]*4, [0.0]*6
        dt = (datetime.datetime.now() - self.ref_time).total_seconds()
        finished = True
        for traj in self.trajectories:
            cmd, t_ended = self.trajectories[traj].get_cmd_vel(dt)
            finished &= t_ended
            if traj in self.cosmetic_name_idx:
                cos_j[self.cosmetic_name_idx[traj]] = cmd
            elif traj in self.kinematic_name_idx:
                kin_j[self.kinematic_name_idx[traj]] = cmd
        if finished:
            return None
        else:
            return kin_j, cos_j

    @classmethod
    def from_dict(cls, data):
        """
        {'joint_a': {'time': [t1, t2, t3], 'position': [p1, p2, p3]}}
        """
        trajectories = {}
        for j in data:
            t_, p_ = [], []
            for t, p in zip(data[j]['times'], data[j]['positions']):
                t_.append(t)
                p_.append(t)
            trajectories[j] = Trajectory(angles=p_, times=t_)

        return cls(trajectories=trajectories)


class NodeAnimationPlayer(node.Node):
    def __init__(self, app):
        super(NodeAnimationPlayer, self).__init__(app, 'AnimationPlayer')
        self.playing_animations = []
        self.current_animation = None
        self.animation_running = app.animation_running
        # Kinematics target joint positions (config in the MDK)
        self.config = [0.0] * 4

    def play_animation(self, anim):
        if self.playing_animations:
            self.playing_animations.append(anim)

    def get_config(self):
        return self.config

    def tick(self):

        """ Calculate next step in the animation."""

        if not self.current_animation:
            if self.playing_animations:
                self.current_animation = self.playing_animations.pop(0)
                self.current_animation.initialize(self.sys.input.sensors_package.kinematic_joints.position)

        else:
            cmds = self.current_animation.get_commands()
            if cmds:
                self.animation_running = True
                self.config = cmds[0]
                self.output.cosmetic_joints = cmds[1]
            else:
                self.animation_running = False
                self.current_animation = None
