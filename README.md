# ReadingToRobot

Checking the efficacy of reading to robot as a support for teachers in engaging kids with reading

## Requirement Setup

Each robot has some specific setup requirements:

### Cozmo

The setup for Cozmo requires a mobile phone or tablet with the Cozmo App.
You can find this app in Google's PlayStore or Apple's AppStore.

Then, you need to install ADB and Python3.
If you are using a linux machine, you already will have Python3 installed, and you can add ADB by
running the following commands:

```
sudo apt update && sudo apt install android-tools-adb
```

### MiRo

MiRo is controlled via ROS, so you'll need to install ROS in your computer to run it.
Because of this, we recommend using a linux distribution compatible with the latest version of ROS,
like Ubuntu 20.04.

See instructions to install ROS in your computer in: http://wiki.ros.org/Installation/Ubuntu

### NAO

You need the NAOqi 2.8 Python SDK to be able to control NAO.
Please follow the instructions in http://doc.aldebaran.com/2-8/dev/python/install_guide.html to
install it in your machine.

Please notice that NAOqi 2.8 Python SDK is only compatible with Python2.7.
This means that you will need to install this version of Python in your machine.

Also, the NAOqi Python SDK is composed mainly of bindings for the C++ SDK.
This library does not contain binaries for arm targets, meaning that the Python SDK cannot run in a
Raspberry Pi.

If you are going to use a Raspberry Pi, you can install this package on NAO's own computer, and run
it remotely.
To do so, please follow the instructions to isnstall a virtual environment in NAO's computer
provided in [this repository](https://github.com/NaoPepper4hri/nao_virtualenv).
Once this environment is running, you can freely install this and any other packages in NAO's head.

### Common

No matter which robot you are using, you'll need to install a couple of dependencies to run this
package.
You will also need to download the ReadingToRobot package:

```
git clone https://github.com/chaudhuryB/ReadingToRobot.git
cd ReadingToRobot
```

For python3 setups (MiRo, Cozmo), run the following command:

```
python3 -m pip install -r requirements.txt
```

For python2 setups (NAO):

```
python2 -m pip install -r requirements2.txt
```

And if you are using all, run both commands.

You will also need to install a MQTT server in your machine, to handle the messaging between
different process in the package:

```
sudo apt update && sudo apt install mosquitto
```

## Package installation

Once the requirements are installed, you can install this package by running:

```
cd <path-to-repository>
python3 -m pip install .

(or for python2 setups)
python2 -m pip install .
```

## Usage

After installing this package, a few different scripts will be available in your machine.

The robot control should be launched separately from the speech recognition, meaning that to start
an interaction with a robot, you need to:

1. Launch the robot controller.

   You can do this directly with:

   ```
   read_to_robot <robot-name> [--options]
   ```

   Or using the robot specific launch scripts: `launch_miro`, `launch_nao`.
   Examples:

   ```
   launch_nao <NAO's IP>
   ```

   ```
   launch_miro <MIRO's IP>
   ```

2. Launch the speech service:
   ```
   speech_service.py
   ```

Optionally, the robot can be controlled by publishing directly to MQTT, in the following form:

```
mosquitto_pub -t "speech/cmd" -m "happy"
```
