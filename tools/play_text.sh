#!/bin/bash

if [[ -f "$1" ]]
then
    if [ ${1: -4} == ".txt" ]
    then
        cat $1 | xargs -I {} espeak --stdout {} -s 100 -g 5 | aplay
    else
        aplay $1
    fi
else
    espeak --stdout "$@" -s 100 -g 5 | aplay
    sleep 5
fi
