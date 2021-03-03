#!/bin/bash

docker run --env MIRO_ROBOT_IP=$1 --device /dev/snd:/dev/snd --network="host" -it reading bash -c "source /root/mdk/setup.bash && read_to_miro"
