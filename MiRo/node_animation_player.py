
import datetime
from miro2.core import node


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
        # For now, the trajectory will keep a constant speed between positions.
        for i, cmd in enumerate(self.anim_cmds):
            if self.times[i+1] > t:
                return cmd
        return None

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
        pass

    def get_cmd_vel(self):
        return None


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
        jnts = []
        dt = (datetime.datetime.now() - self.ref_time).total_seconds()
        finished = True
        for traj in self.trajectories:
            cmd = traj.get_cmd_vel(dt)
            if cmd is None:
                jnts.append(0.0)
            else:
                jnts.append(cmd)
                finished = False
        if finished:
            return None
        else:
            return jnts

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
    def __init__(self, sys):
        super(NodeAnimationPlayer, self).__init__(sys, 'AnimationPlayer')
        self.playing_animations = []
        self.current_animation = None

    def play_animation(self, anim):
        if self.playing_animations:
            self.playing_animations.append(anim)

    def tick(self):

        """ Calculate next step in the animation."""

        if not self.current_animation:
            if self.playing_animations:
                self.current_animation = self.playing_animations.pop(0)
                self.current_animation.initialize(self.sys.input.sensors_package.kinematic_joints.position)
            else:
                return
        else:
            kin_jnt, cos_jnt = self.current_animation.get_commands()
