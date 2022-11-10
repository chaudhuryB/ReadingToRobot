# ReadingToRobot

Checking the efficacy of reading to robot as a support for teachers in engaging kids with reading.

See specific steps for each robot in [Installation](./doc/installation.md).

For information about the robots' movements, see [Design](./doc/design.md).

## Usage

After installing this package, a few different scripts will be available on your machine.

The robot control should be launched separately from the speech recognition, meaning that to start
an interaction with a robot, you need to:

1. Launch the robot controller.

   You can do this directly with:

   ```
   read_to_robot <robot-name> [--options]
   ```

   Or using the robot-specific launch scripts: `launch_miro`, `launch_nao`.
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
