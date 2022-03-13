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

import argparse
import paho.mqtt.client as mqtt
import json
import logging
from gpiozero import OutputDevice
from socket import gethostname

# The IR filter is on pin 5
ir_filter = OutputDevice(5)

DEFAULT_MQTT_BROKER_IP = "10.0.0.5"
DEFAULT_MQTT_BROKER_PORT = 1883
DEFAULT_MQTT_TOPIC = "IR_filter"
DEFAULT_MQTT_ACTION = "toggle"


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

parser = argparse.ArgumentParser(
    description = "Receive commands for IR cut-filter."
    )
parser.add_argument(
    "--broker",
    default=DEFAULT_MQTT_BROKER_IP,
    type=str,
    help="mqtt broker port",
    )
parser.add_argument(
        "--port",
        default=DEFAULT_MQTT_BROKER_PORT,
        type=int,
        help="mqtt broker port",
    )
parser.add_argument(
        "--topic",
        default=DEFAULT_MQTT_TOPIC,
        type=str,
        help="mqtt topic"
    )
args = parser.parse_args()


client = mqtt.Client(gethostname())
client.on_connect = on_connect
client.on_message = on_message
client.connect(DEFAULT_MQTT_BROKER_IP, DEFAULT_MQTT_BROKER_PORT)
client.loop_forever()
