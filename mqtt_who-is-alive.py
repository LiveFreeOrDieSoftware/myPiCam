#!/usr/bin/python

"""
Who is Alive
Listens for mqtt messages from up to 7 hosts
Records host data in a list
Displays status on leds on a Unicorn pHAT
"""

import unicornhat as uh
import paho.mqtt.client as mqtt
import json
import colorsys
import logging
from datetime import datetime, timedelta
import time, threading

# logging can also write to file, and call also fill your drive
# logging.basicConfig(filename='who_is_alive.log', format=%(levelname)s:%(message)s', level=logging.INFO)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Need to set some things up for the Pimoroni Autiomation pHAT
uh.set_layout(uh.PHAT)
uh.brightness(0.4)

# initalize a list for host data, and making it GLOBAL
global hosts_list
# when i first wrote this i had a long, typed-out list of dictionaries
# thanks to the magic of list comprehensions
hosts_list = [({'hostid': 'host' + str(x)}) for x in range(8)]
# these logging statements will let you see if the list was created correctly
logging.info("Hosts_list created")
for item in hosts_list:
    logging.debug(item)

def on_connect(client, userdata, flags, rc):
    logging.info("OnConnect:  Connected with result code {0}".format(str(rc)))
    client.subscribe("IamAlive")
    threadCount()

# onMessage passes the IamAlive data to other functions
def on_message(client, userdata, msg):
    values = json.loads(msg.payload)
    hostid = int(values["id"])
    logging.debug("OnMessage:  hostid:  %s, message:  %s", hostid, values)
    update_hosts(hostid, values)

# The message is passed to this function which updates the global hosts_list
def update_hosts(hostid, values):
    logging.debug("UpdateHosts:  HostID:  %s, values:  %s", hostid, values)
    # The default in the pub script is hostid 0, which is reserved for ? something
    if hostid == 0:        # hostid 0 indicates a misconfigured client
        for i in range(4):
            uh.set_pixel(0,i,255,0,0)
        uh.show()
        hosts_list[0]["timestamp"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
        logging.info("UpdateHosts:  Host0 timestamp updated")
    else:
        hosts_list[hostid] = values
        # it used to call update_health from hear, but want that on a timer
        # instead of triggered by messages


# i need something to do the threading
# the name doesn't mean anything. it doesnt really count. i just liked the name
def threadCount():
    update_health()
    threading.Timer(1, threadCount).start()


"""
UpdateHealth does compares a current timestamp with the data for each host.
This compares the last message timestamp with a delta of the current.
The comparison tests old + delta < new.
"""
def update_health():
    new_timestamp = datetime.now()
    logging.debug("UpdateHealth:  newtimestamp: %s, hosts_list: %s ", new_timestamp, hosts_list)
    for i in range(8):
        try:
            old_timestamp = datetime.strptime((hosts_list[i]['timestamp']), "%Y%m%d %H:%M:%S")
            logging.debug("UpdateHealth:  HostID %s  old_timestamp %s", i, old_timestamp)

            # Is this HostID 0? a misconfigured client
            if i == 0:
                logging.debug("Made it to the hosts0 loop in UpdateHealth!!!!!!!!")
                if (old_timestamp + timedelta(seconds = 30)) < new_timestamp:
                    for i in range(4):
                        uh.set_pixel(0,i,0,0,0)
                    uh.show()
                    hosts_list[0] = {"id":"0","health":"no data"}
                    logging.debug("UpdateHealth:  Host0 RESET")
            
            # Over 5 minutes health is RED
            elif (old_timestamp + timedelta(minutes = 5)) < new_timestamp:
                logging.debug("UpdateHealth:  Health of %s is RED!", i)
                hosts_list[i]["health"] = 'red'
                uh.set_pixel(i,0,255,0,0)

            # Over 1 minute health is YELLOW
            elif (old_timestamp + timedelta(minutes = 1)) < new_timestamp:
                logging.debug("UpdateHealth:  Health of %s is YELLOW.", i)
                hosts_list[i]["health"] = 'yellow'
                uh.set_pixel(i,0,255,255,0)

            # else health is GREEN
            else:
                logging.debug("UpdateHealth:  time_diff + 1m is MORE than new_timestamp. Health is GREEN!")
                hosts_list[i]["health"] = 'green'
                uh.set_pixel(i,0,0,255,0)

        except:
            if i == 0:
                # host0 is expected to have no data
                logging.debug("UpdateHealth:  except:  HostID %s:  no data.", i)
            else:
                # the other hosts are expected to have data
                logging.info("UpdateHealth:  except:  HostID %s: no data.", i)

        # trying to call set_color from here
        logging.debug("UpdateHealth:  trying to call set_color for %s", i)
        set_color(i)

# after health is set we need to go throug the other measurements
def set_color(hostid):
    logging.debug("SetColor:  HostID:  %s got to set_color", hostid)
    # doing the no_data next will prevent them from being
    # sent to functions that loof for data that won't be there
    try:
        if hosts_list[hostid]['health'] == 'no_data':
            for i in range(4):
                uh.set_pixel(hostid, i, 0, 0, 0)
                uh.show()
        else:
            set_temp_color(hostid)
            set_disk_color(hostid)
            set_cpu_usage_color(hostid)
            uh.show()
    except:
        pass

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
    if disk_percentage > 90:
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
