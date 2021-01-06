#!/bin/bash

espeak --stdout "$@" -s 100 -g 5 | aplay

sleep $#