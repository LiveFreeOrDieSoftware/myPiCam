#!/bin/bash
# used with RPi Cam Web Interface
# put in the macros folder
# can be called by the scheduler

TIMESTAMP=$(date +"%T")
HOSTNAME=$(hostname)

mosquitto_pub -h 10.0.0.5 -t IR_filter -m '{"action": "on"}'

