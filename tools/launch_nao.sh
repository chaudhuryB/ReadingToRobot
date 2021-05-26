#!/bin/bash

ip=$(hostname -I | awk '{print $1}')

cmd="source /home/nao/venv/bin/activate && read_to_robot nao --mqttIP ${ip}"

sshpass -p "${NAO_PASSWORD}" ssh -o "StrictHostKeyChecking accept-new" nao@$1 ${cmd}
