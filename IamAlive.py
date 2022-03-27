#!/usr/bin/python
"""
This script publishes an mqtt message periodically.
It is intended to be the heartbeat for a watchdog service
which would be an mqtt subscriber.

It currently collects various system data and packs it in
a Python dictionary that is send as json in the mqtt message.
"""
# I don't know what I am doing down below
# Everything is in functions
# even stuff that really doesn't need to be?!?!@#&

import argparse
import shutil
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import datetime
import logging

from subprocess import PIPE, Popen, check_output
import time
import socket

# I want to add filename= below, but it won't start from systemd with it
# need to figure out logfiles, locations, permissions, etc.
# logging.basicConfig(filename='IamAlive.log', format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

DEFAULT_MQTT_BROKER_IP = "10.0.0.5"
DEFAULT_MQTT_BROKER_PORT = 1883
DEFAULT_MQTT_TOPIC = "IamAlive"
DEFAULT_READ_INTERVAL  = 15
DEFAULT_HOSTID = 0
# client_id = f'python-mqtt-{random.randint(0, 1000)}'


# mqtt callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("OnConnect:  connected OK")
    else:
        logging.info("Bad connection Returned code=", rc)


def on_publish(client, userdata, mid):
    logging.debug("mid: " + str(mid))


def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        C = (float(f.read()) / 1000)
        f.close()
        logging.debug(f'getCpuTemp:  The CPU temp in C is: {C}')
        return C

def get_cpu_usage(nproc):
    loadavg = list(open('/proc/loadavg').read().strip().split())
    load = float(loadavg[0])/nproc
    return load


def get_disk_usage():
    values = {}
    BytesPerGB = 1024 * 1024 * 1024
    (total, used, free) = shutil.disk_usage("/")
    values["disk-total"] = ("%.2f" % (float(total)/BytesPerGB))
    values["disk-used"] = ("%.2f" % (float(used)/BytesPerGB))
    values["disk-free"] = ("%.2f" % (float(free)/BytesPerGB))
    logging.debug(f'getDiskUsage:  {values}')
    return values
    
# I could have done this in one line if I had put this
# as the variable assignment...
def get_hostname():
    hostname = socket.gethostname()
    logging.debug(f'getHostname:  The hostname is: {hostname}')
    return hostname

# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()

# Main loop
# Taking arguements is probably pretty heavy for this script
# which is really meant to run as a service. Dealing with 
# hostid is tricky, though, as it is not derived from any
# system value, and tweaking the script messes with Git

def main():
    parser = argparse.ArgumentParser(
        description="Publish RPi values over mqtt") 
    parser.add_argument(
        "--broker",
        default=DEFAULT_MQTT_BROKER_IP,
        type=str,
        help="mqtt broker IP",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_MQTT_BROKER_PORT,
        type=int,
        help="mqtt broker port",
    )
    parser.add_argument(
        "--topic", default=DEFAULT_MQTT_TOPIC, type=str, help="mqtt topic"
    )
    parser.add_argument(
        "--interval",
        default=DEFAULT_READ_INTERVAL,
        type=int,
        help="the read interval in seconds",
    )
    parser.add_argument(
        "--hostid",
        default=DEFAULT_HOSTID,
        type=int,
        help="the ID of the host at the monitor",
    )
    args = parser.parse_args()

    # Raspberry Pi ID
    hostname = get_hostname()
    device_serial_number = get_serial_number()
    device_id = "raspi-" + device_serial_number
    hostid = int(args.hostid)

    nproc = int(check_output('nproc').decode('UTF-8').strip())


    logging.info(
        f"""IamAlive.py - Sends cpu temp and system info over mqtt.

    broker: {args.broker}
    client_id: {device_id}
    port: {args.port}
    topic: {args.topic}
    hostid: {args.hostid}

    Press Ctrl+C to exit!

    """
    )

    mqtt_client = mqtt.Client(client_id=device_id)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.connect(args.broker, port=args.port)


    # Main loop to read data, display, and send over mqtt
    mqtt_client.loop_start()
    while True:
        try:
            logging.debug('Main loop begin.')
            values = get_disk_usage()
            values["cpu_temp"] = get_cpu_temp()
            values["cpu_usage"] = get_cpu_usage(nproc)
            values["serial"] = device_serial_number
            values["hostname"] = hostname
            values["timestamp"] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S") 
            values["id"] = args.hostid
            logging.debug(f'Main loop: {values}')
            mqtt_client.publish(args.topic, json.dumps(values))
            time.sleep(args.interval)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

