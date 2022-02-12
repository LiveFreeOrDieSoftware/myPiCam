#!/bin/bash
# used with RPi Cam Web Interface
# put in the macros directory (/var/www/html/macros/)
# from cam-11

TIMESTAMP=$(date +"%T")
HOSTNAME=$(hostname)

mosquitto_pub -h 10.0.0.5 -t IR_filter -m '{"action": "off"}'

