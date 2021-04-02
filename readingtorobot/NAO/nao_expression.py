
##
# This file contains timelines for different movements of NAO robot

def get_scared_movement():
    names = list()
    times = list()
    keys = list()

    names.append("LElbowRoll")
    times.append([0.16])
    keys.append([-0.954695])

    names.append("LHipPitch")
    times.append([0.16])
    keys.append([-1.44862])

    names.append("LShoulderRoll")
    times.append([0.16])
    keys.append([0.20848])

    names.append("RElbowRoll")
    times.append([0.16])
    keys.append([0.963422])

    names.append("RHipPitch")
    times.append([0.16])
    keys.append([-1.44862])

    names.append("RShoulderRoll")
    times.append([0.16])
    keys.append([-0.218166])

    return names, keys, times


def get_annoyed_movement():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([0.96])
    keys.append([0.096262])

    names.append("HeadYaw")
    times.append([0.96])
    keys.append([-0.298673])

    names.append("LElbowRoll")
    times.append([0.96])
    keys.append([-0.954695])

    names.append("LHipPitch")
    times.append([0.96])
    keys.append([-1.44862])

    names.append("LShoulderRoll")
    times.append([0.96])
    keys.append([0.20848])

    names.append("RElbowRoll")
    times.append([0.96])
    keys.append([0.963422])

    names.append("RHipPitch")
    times.append([0.96])
    keys.append([-1.44862])

    names.append("RShoulderRoll")
    times.append([0.96])
    keys.append([-0.218166])

    return names, keys, times


def get_excited_movement():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([0.16, 0.28, 0.52, 0.68, 0.96])
    keys.append([-0.0820305, -0.174533, -0.0925025, -0.1309, -0.0907571])

    return names, keys, times


def get_sad_movement():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([1.56])
    keys.append([0.513127])

    return names, keys, times


def get_dab_movement():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([0.733333, 1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([-0.21293, 0.514872, 0.397935, 0.397933, 0.453438, -0.161121])

    names.append("HeadYaw")
    times.append([0.733333, 1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([-0.0453786, -0.3735, 0.121444, 0.121449, 0.131913, -0.00517979])

    names.append("LElbowRoll")
    times.append([0.866667, 1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([-0.849975, -1.54462, -1.34282, -1.31706, -1.39383, -0.872665])

    names.append("LElbowYaw")
    times.append([1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0, -0.342282, -0.347581, -0.219484, -0.129154])

    names.append("LHand")
    times.append([0.866667, 1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.08, 0.602755, 0.991413, 0.991408, 0.599794, 0.304406])

    names.append("LShoulderPitch")
    times.append([0.866667, 1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.195477, -0.403171, 0.00964282, 0.0152586, -0.100026, 0.733038])

    names.append("LShoulderRoll")
    times.append([1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.139697, -0.10536, -0.07895, -0.00176048, 0])

    names.append("LWristYaw")
    times.append([0.866667, 1.53333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([-0.7662, 0, -0.000473026, -0.000455733, -0.00282106, 0.0946637])

    names.append("RElbowRoll")
    times.append([0.733333, 1.4, 2.26667, 2.33333, 2.86667, 4.06667, 5.33333])
    keys.append([1.24791, 0.534071, 0.0380194, 0.0349066, 0.0387634, 0.878332, 1.42942])

    names.append("RElbowYaw")
    times.append([0.733333, 1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([1.42244, 1.2363, 0.751108, 0.75825, 1.22859, 0.204204])

    names.append("RHand")
    times.append([0.733333, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.66, 1, 0.999995, 0.976061, 0.306778])

    names.append("RShoulderPitch")
    times.append([0.733333, 1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.79587, 0.53058, -0.652284, -0.652718, -0.161813, 0.731293])

    names.append("RShoulderRoll")
    times.append([1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.219786, -1.03848, -1.04119, -0.507324, -0.750492])

    names.append("RWristYaw")
    times.append([0.733333, 1.4, 2.26667, 2.86667, 4.06667, 5.33333])
    keys.append([0.493928, -1.27409, -1.19082, -1.1971, -1.2663, 0.0970475])

    return names, keys, times


def get_arms_up():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([0.6, 2.76])
    keys.append([-0.234621, -0.189354])

    names.append("HeadYaw")
    times.append([0.6, 2.76])
    keys.append([0, 0])

    names.append("LElbowRoll")
    times.append([0.6, 2.76])
    keys.append([-1.0573, -0.872665])

    names.append("LElbowYaw")
    times.append([0.6, 2.76])
    keys.append([-1.19953, -0.129154])

    names.append("LHand")
    times.append([0.6, 2.76])
    keys.append([0.577628, 0.577628])

    names.append("LShoulderPitch")
    times.append([0.6, 2.76])
    keys.append([-0.736971, 0.733038])

    names.append("LShoulderRoll")
    times.append([0.6, 2.76])
    keys.append([0.18997, 0])

    names.append("LWristYaw")
    times.append([0.6, 2.76])
    keys.append([0.100148, 0.0908224])

    names.append("RElbowRoll")
    times.append([0.6, 2.76])
    keys.append([1.06741, 1.42942])

    names.append("RElbowYaw")
    times.append([0.6, 2.76])
    keys.append([1.19953, 0.204204])

    names.append("RHand")
    times.append([0.6, 2.76])
    keys.append([0.580799, 0.580799])

    names.append("RShoulderPitch")
    times.append([0.6, 2.76])
    keys.append([-0.736971, 0.731293])

    names.append("RShoulderRoll")
    times.append([0.6, 2.76])
    keys.append([-0.181565, -0.750492])

    names.append("RWristYaw")
    times.append([0.6, 2.76])
    keys.append([0.096694, 0.0876897])

    return names, keys, times


#################################################
# Background movements

def get_background_A():
    names = list()
    times = list()
    keys = list()

    names.append("LElbowRoll")
    times.append([1])
    keys.append([-0.872665])

    names.append("LShoulderPitch")
    times.append([1])
    keys.append([0.813323])

    names.append("LShoulderRoll")
    times.append([1])
    keys.append([0])

    names.append("RElbowRoll")
    times.append([1])
    keys.append([0.74351])

    names.append("RShoulderPitch")
    times.append([1])
    keys.append([0.813323])

    names.append("RShoulderRoll")
    times.append([1])
    keys.append([0])

    return names, keys, times


def get_background_B():
    names = list()
    times = list()
    keys = list()

    names.append("LElbowRoll")
    times.append([0.96])
    keys.append([-1.40674])

    names.append("LElbowYaw")
    times.append([0.96])
    keys.append([-0.129154])

    names.append("LShoulderPitch")
    times.append([0.96])
    keys.append([0.733038])

    names.append("LShoulderRoll")
    times.append([0.96])
    keys.append([0.747001])

    names.append("RElbowRoll")
    times.append([1.52])
    keys.append([0.74351])

    names.append("RShoulderPitch")
    times.append([1.52])
    keys.append([0.767945])

    names.append("RShoulderRoll")
    times.append([1.52])
    keys.append([0])

    return names, keys, times


def get_background_C():
    names = list()
    times = list()
    keys = list()

    names.append("LElbowRoll")
    times.append([1.6])
    keys.append([-0.872665])

    names.append("LShoulderPitch")
    times.append([1.6])
    keys.append([0.733038])

    names.append("LShoulderRoll")
    times.append([1.6])
    keys.append([0])

    names.append("RElbowRoll")
    times.append([0.96])
    keys.append([1.42942])

    names.append("RElbowYaw")
    times.append([0.96])
    keys.append([0.204204])

    names.append("RShoulderPitch")
    times.append([0.96])
    keys.append([0.731293])

    names.append("RShoulderRoll")
    times.append([0.96])
    keys.append([-0.750492])

    return names, keys, times


def get_looking_down():
    names = list()
    times = list()
    keys = list()

    names.append("HeadPitch")
    times.append([0.7])
    keys.append([0.513127])

    names.append("HeadYaw")
    times.append([0.7])
    keys.append([0.0])

    return names, keys, times


# Base pose transitions
def go_to_fwd_lean():
    names = list()
    times = list()
    keys = list()

    names.append("LAnklePitch")
    times.append([3.12])
    keys.append([-0.0436332])

    names.append("LAnkleRoll")
    times.append([3.12])
    keys.append([-0.141372])

    names.append("LHipPitch")
    times.append([3.12])
    keys.append([-1.48004])

    names.append("LHipRoll")
    times.append([3.12])
    keys.append([-0.0436332])

    names.append("LHipYawPitch")
    times.append([3.12])
    keys.append([-0.694641])

    names.append("LKneePitch")
    times.append([3.12])
    keys.append([-0.0296706])

    names.append("LShoulderPitch")
    times.append([0.84])
    keys.append([0.610865])

    names.append("RAnklePitch")
    times.append([3.12])
    keys.append([0.20944])

    names.append("RAnkleRoll")
    times.append([3.12])
    keys.append([-0.0279253])

    names.append("RHipPitch")
    times.append([3.12])
    keys.append([-1.53589])

    names.append("RHipRoll")
    times.append([3.12])
    keys.append([-0.479966])

    names.append("RHipYawPitch")
    times.append([3.12])
    keys.append([-0.694641])

    names.append("RKneePitch")
    times.append([3.12])
    keys.append([-0.0925025])

    names.append("RShoulderPitch")
    times.append([0.84])
    keys.append([0.623083])

    return names, keys, times
