# ReadingToRobot
Checking the efficacy of reading to robot as a support for teachers in engaging kids with reading



## Requirement

Tabled running adb bridge and Como version 1.5 installed

For Cozmo python3.5 and the following packages installed

cozmo==0.14.0

cozmoclad==1.5.0

numpy==1.16.4

Pillow==6.1.0

pocketsphinx==0.1.15

PyAudio==0.2.11

SpeechRecognition==3.8.1

There is a new event added to the world.py in the cozmo sdk libraries from Anki. The modified world.py used for the Cozmo has been provided. The event is used to pick up on the delocalization of the Cozmo robot once the fist bump reward is activated.


## Setup

To support all robots in a single installation, we recommend using OS versions compatible with ROS Kinetic, like Ubuntu 16.04.
If you are using a Raspberry Pi to run this experiment, you can find different versions of Ubuntu 16.04 for raspberry following this link:
https://releases.ubuntu-mate.org/archived/16.04/armhf/

Different steps must be followed for installation of the necessary software for each robot.

