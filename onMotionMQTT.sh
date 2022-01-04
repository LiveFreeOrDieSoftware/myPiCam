#!/bin/bash 

TIMESTAMP=$(date +"%T") 
HOSTNAME=$(hostname)

mosquitto_pub -h 10.0.0.5 -t motion -m "timestamp:$TIMESTAMP, host:$HOSTNAME, message: Motion On" 
