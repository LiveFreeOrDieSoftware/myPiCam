#!/usr/bin/python

# mqtt_who-is-alive.py
# this is an attempt to collect system information from mqtt
# and display it on a Pimoroni Unicorn pHAT

# the mqtt is from from digi.com

import unicornhat as uh
import paho.mqtt.client as mqtt
import json
import colorsys
import logging
# need to learn why other forms of importind datetime did not work
from datetime import datetime, timedelta
from time import sleep

# logging.basicConfig(filename='who_is_alive.log', format='%(levelname)s:%(message)s', level=logging.INFO)
# when working things out I found it easier to NOT log to a file
# the file is good for debugging the service; it can grow fast
# and the path is relative, and pi cannot stat a file where it would drop
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

uh.set_layout(uh.PHAT)
uh.brightness(0.4)

# initialize a list for host data, and making it GLOBAL!
# There are lots of bad vibes about globals, but it makes things work here.
global hosts_list
# there must be a more elegant way to do this
hosts_list = [{'hostid':'host0'}, {'hostid':'host1'}, {'hostid':'host2'}, {'hostid':'host3'}, {'hostid':'host4'}, {'hostid':'host5'}, {'hostid':'host6'}, {'hostid':'host7'}]
logging.info("Hosts_list created")
for item in hosts_list:
    logging.debug(item)


def on_connect(client, userdata, flags, rc):
    logging.info("OnConnect:  Connected with result code {0}".format(str(rc)))
    client.subscribe("IamAlive")

# OnMessage passes the IamAlive data to other functions
def on_message(client, userdata, msg):
    values =  json.loads(msg.payload)
    hostid = int(values["id"])
    logging.debug("OnMessage:  hostid:  %s, message:  %s", hostid, values)
    update_hosts(hostid, values)


# The message is passed to this function which updates the GLOBAL list
def update_hosts(hostid, values):
    logging.debug("UpdateHosts:  HostID:  %s,  values:  %s", hostid, values)
    # The default in the pub script is hostid 0, which is reserved for ? something
    if hostid == 0:  # hostid 0 indicates a misconfigured client
        for i in range(4):
            uh.set_pixel(0,i,255,0,0)
        uh.show()
        hosts_list[0]["timestamp"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
        logging.info("UpdateHosts:  Host0 timestamp updated")
    else:
        hosts_list[hostid] = values
        update_health(hostid)
        logging.info("UpdateHosts:  HostID:  %s, after update_health about to set_color:  %s", hostid, hosts_list[hostid]['health'])
        if hosts_list[hostid]['health'] == 'green':
            set_color(hostid)
        else:
            pass

# with every message we check every host's health, we need to know when we DO NOT get an update
def update_health(hostid):
    new_timestamp = datetime.now()
    logging.debug("UpdateHealth:  new_timestamp: %s, hosts_list: %s ", new_timestamp, hosts_list)
    for i in range(8):
        try:
            old_timestamp = datetime.strptime((hosts_list[i]['timestamp']), "%Y%m%d %H:%M:%S")
            logging.info("UpdateHealth:  HostID %s  old_timestamp %s", i, old_timestamp)

            # Is this HostID 0?  A misconfigured client
            if i == 0:
                logging.info("Made it to the host0 loop in updatehealth!!!!!!$$$$$####")
                if (old_timestamp + timedelta(seconds = 30)) < new_timestamp:
                    for i in range(4):
                        uh.set_pixel(0,i,0,0,0)
                    uh.show()
                    hosts_list[0] = {"id":"0","health":"no data"}
                    logging.info("UpdateHealth: Host0 RESET") 
            
            # Over 5 minutes health is RED
            elif (old_timestamp + timedelta(minutes = 5)) < new_timestamp:
                logging.info("UpdateHealth:  Health of %s is RED!", i)
                hosts_list[i]["health"] = 'red'
                uh.set_pixel(i,0,255,0,0)

            # Over 1 minute health is YELLOW
            elif (old_timestamp + timedelta(minutes = 1)) < new_timestamp:
                logging.info("UpdateHealth:  Health of %s is YELLOW!", i)
                hosts_list[i]["health"]  = 'yellow'
                uh.set_pixel(i,0,255,255,0)

            # else health is GREEN
            else:
                logging.debug("UpdateHealth:  time_diff + 1m is MORE than new_timestamp. Health is GREEN!")
                hosts_list[i]["health"] = 'green'
                uh.set_pixel(i,0,0,255,0)

        except:
            logging.info("UpdateHealth: except:  HostID %s:  no data.", i)


# after health is set we need to go through the other measurements
def set_color(hostid):
    logging.debug("SetColor:  HostID:  %s got to set_color", hostid)
    # doing the no_data next will prevent them from being
    # sent to functions that look for data that won't be there
    if hosts_list[hostid]['health'] == 'no_data':
        for i in range(4):
            uh.set_pixel(hostid, i, 0, 0, 0)
            uh.show()
    else:
        set_temp_color(hostid)
        set_disk_color(hostid)
        set_cpu_usage_color(hostid)
        uh.show()

# set the color for the CPU temperature
def set_temp_color(hostid):
    logging.debug("SetTempColor:  HostID: %s: got HERE!!!", hostid)
    timestamp = hosts_list[hostid]['timestamp']
    hostname = hosts_list[hostid]['hostname']
    temp = hosts_list[hostid]['cpu_temp']
    # Necessary to stay 'red' when the temp tops our color range
    if temp > 70:
        temp = 70
    hue = (70 - temp) / 100
    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
    uh.set_pixel(hostid, 1, r, g, b)

def set_cpu_usage_color(hostid):
    logging.debug("SetCPUusageColor:  got here:  HostID: %s", hostid)
    cpu_usage = hosts_list[hostid]['cpu_usage']
    hue = ((cpu_usage*100)/1.41)+33 / 100
    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
    uh.set_pixel(hostid, 3, r, g, b)


def set_disk_color(hostid):
    logging.debug("SetDiskColor:  HostID: %s:  arrived!", hostid)
    disk_percentage = int((float(hosts_list[hostid]["disk-used"]) / float(hosts_list[hostid]["disk-total"])) * 100)
    logging.debug("SetDiskColor:  HostID: %s:  disk_percentage: %s", hostid, disk_percentage)
    if disk_percentage >90:
        logging.debug("SetDiskColor:  HostID: %s:  disk health is RED", hostid)
        uh.set_pixel(hostid, 2, 255, 0, 0)
    elif disk_percentage > 75:
        logging.debug("SetDiskColor:  HostID: %s:  disk health is YELLOW", hostid)
        uh.set_pixel(hostid, 2, 255, 165, 0)
    else:
        logging.debug("SetDiskColor:  HostID: %s:  disk health is GREEN", hostid)
        uh.set_pixel(hostid, 2, 0, 255, 0)


client = mqtt.Client("mqtt_iamalive_teston-BB")
client.on_connect = on_connect
client.on_message = on_message
client.connect('10.0.0.5', 1883)
client.loop_forever()
