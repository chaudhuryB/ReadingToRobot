#!/bin/bash

ip=$(hostname -I | awk '{print $1}')

cmd="source /home/nao/venv/bin/activate && read_to_NAO --speechIP ${ip} --speechPort 44111"

sshpass -p "${NAO_PASSWORD}" ssh nao@${NAO_IP} ${cmd}
