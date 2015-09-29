#!/bin/bash

modprobe bcm2835-v4l2

while true
do
    python /app/main.py
    sleep 5
done
