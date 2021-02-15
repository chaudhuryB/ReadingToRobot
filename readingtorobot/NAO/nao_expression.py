
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
