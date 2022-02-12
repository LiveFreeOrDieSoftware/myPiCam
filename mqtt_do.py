#!/usr/bin/python

"""
This is a variation of the Unicorn script
where I learned to pass mqtt message data to functions.
Here I want to control the IR cut-filter with mqtt messages
that can be generated, for instance from RPi Cam Web Int.

There are a bunch of hard-coded bad bits in here than need 
a strategy
"""
# the mqtt is from from digi.com

import paho.mqtt.client as mqtt
import json
import logging
from gpiozero import OutputDevice

# The IR filter is on pin 5
ir_filter = OutputDevice(5)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def on_connect(client, userdata, flags, rc):
    logging.info("OnConnect:  Connected with result code {0}".format(str(rc)))
    client.subscribe("IR_filter")


def on_message(client, userdata, msg):
    logging.info("OnMessage:  Message received-> " + msg.topic + " " + str(msg.payload))
    values =  json.loads(msg.payload)
    logging.debug("OnMessage:  The converted dictionary is : " + str(values))
    logging.debug("OnMessage:  The type is: " + str(type(values)))
    action = (values["action"])
    ir_filter_control(action)

def ir_filter_control(action):
    logging.debug("IR filter control: Action received = " + str(action))
    if action == 'on':
        ir_filter.on()
    elif action == 'off':
        ir_filter.off()
    elif action == 'toggle':
        ir_filter.toggle()
    else:
        logging.warning("IR filter control: action out of bounds")




client = mqtt.Client("cam-11")
client.on_connect = on_connect
client.on_message = on_message
client.connect('10.0.0.5', 1883)    # hard coding sucks - fix this
client.loop_forever()
