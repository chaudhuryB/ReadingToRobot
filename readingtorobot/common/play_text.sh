#!/bin/bash

if [[ -f "$1" ]]
then
    cat $1 | xargs -I {} espeak --stdout {} -s 100 -g 5 | aplay
else
    espeak --stdout "$@" -s 100 -g 5 | aplay
    sleep 5
fi
