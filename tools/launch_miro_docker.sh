#!/bin/bash

LOCAL_IP=$(hostname -I | awk '{print $1;}')

exec docker run --env MIRO_ROBOT_IP=$1 --env MIRO_LOCAL_IP=$LOCAL_IP \
                --device /dev/snd:/dev/snd --network="host" \
                -v /home/ubuntu/logs:/logs \
                -t reading bash -c "source /root/mdk/setup.bash && read_to_robot miro"
