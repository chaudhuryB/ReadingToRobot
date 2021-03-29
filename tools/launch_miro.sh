#!/bin/bash

export ROS_IP=$(hostname -I | awk '{print $1;}')
export ROS_MASTER_URI=http://$1:11311
read_to_miro
