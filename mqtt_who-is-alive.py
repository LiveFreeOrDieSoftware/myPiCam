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

# logging.basicConfig(filename='who_is_alive.log', format='%(levelname)s:%(message)s', level=logging.INFO)
# when working things out I found it easier to NOT log to a file
# the file is good for debugging the service; it can grow fast
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

uh.set_layout(uh.PHAT)
uh.brightness(0.4)

# initialize a list for host data, and making it GLOBAL!
# There are lots of bad vibes about globals, but it makes things work here.
global hosts_list
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

def update_health():
    new_timestamp = datetime.now()
    for i in range(8):
        try:
            old_timestamp = datetime.strptime((hosts_list[i]["timestamp"]), "Y%m%d %H:%M:%S")
            # If there is not an old_timestamp _except_
            logging.debug("UpdateHosts:  id:  %s, old_timestamp:  %s, new_timestamp:  %s", 
                    i, old_timestamp, new_timestamp)
            
            # Over 5 minutes health is RED
            if (old_timestamp + timedelta(minutes = 5)) < new_timestamp:
                logging.info("UpdateHosts:  Health of %s is RED!")
                hosts_list[i]["health"] = 'red'

            # Over 1 minute health is YELLOW
            elif (old_timestamp + timedelta(minutes = 1)) < new_timestamp:
                logging.info("UpdateHosts:  Health of %s is YELLOW!")
                hosts_list[i]["health"]  = 'yellow'

            # else health is GREEN
            else:
                logging.debug("UpdateHosts:  time_diff + 1m is MORE than new_timestamp. Health is GREEN!")
                hosts_list[i]["health"] = 'green'

        except:
            logging.debug("UpdateHosts: except:  HostID %s:  no data.", i)
            hosts_list[i]["health"] = 'no_data'


def update_hosts(hostid, values):
    logging.debug("UpdateHosts:  HostID:  %s,  values:  %s", hostid, values)

    # update hosts list - before adding health or it gets wiped out
    hosts_list[hostid] = values
    logging.debug("UpdateHosts: hosts_list-hostid: %s", hosts_list[hostid])

    logging.debug("UpdateHosts:  calling update_health next")
    update_health()

    logging.debug("Current content of hosts_list-hostid")
    logging.debug(hosts_list[hostid])
    host_data = (values["timestamp"], values["id"], values["hostname"], values["cpu_temp"])

    logging.debug("calling set_color")
    set_color(host_data)



def set_color(host_data):
    logging.debug("hot to set_color")
    timestamp, hostid, hostname, temp = host_data

    logging.debug("unpacked host_data")
    logging.debug("temp = %s", temp)
    # Necessary to stay 'red' when the temp tops our color range
    if temp > 70:
        temp = 70
    id = int(hostid)
    hue = (70 - temp) / 100
    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
#    logging.debug(f"SetColor:  {hostid} {hostname} is {temp}C and {timestamp}")
#    logging.debug("SetColor:  hosts_list for hostid %s", hostid, hosts_list[hostid])
    for y in range(4):
        uh.set_pixel(id, y, r, g, b)
    uh.show()


client = mqtt.Client("mqtt_iamalive_teston-BB")
client.on_connect = on_connect
client.on_message = on_message
client.connect('10.0.0.5', 1883)
client.loop_forever()
