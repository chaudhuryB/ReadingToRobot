#!/bin/bash
if [[ $1 == 10.3.141.* ]]; then
	ip=10.3.141.1
else
	ip=$(hostname -I | awk '{print $1}')
fi

cmd="source /etc/profile && read_to_robot nao --mqttIP ${ip}"

sshpass -p "${NAO_PASSWORD}" ssh -o "StrictHostKeyChecking accept-new" nao@$1 ${cmd}
