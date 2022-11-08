#!/bin/bash

ip=$(hostname -I | awk '{print $1}')

# MiRo setup
source /opt/ros/noetic/setup.bash
source /home/ubuntu/mdk/setup.bash
export ROS_IP=$ip
export ROS_MASTER_URI=http://$1:11311

# Launch robots
(read_to_robot miro &) &>/dev/null
(read_to_robot cozmo &) &>/dev/null

cmd="source /home/nao/venv/bin/activate && design_reading_buddy_demo --mqttIP ${ip}"
sshpass -p "${NAO_PASSWORD}" ssh -o "StrictHostKeyChecking accept-new" nao@$2 ${cmd}
