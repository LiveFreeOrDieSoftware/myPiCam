import argparse
import shutil
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import datetime

from subprocess import PIPE, Popen, check_output
import time
import socket

DEFAULT_MQTT_BROKER_IP = "10.0.0.5"
DEFAULT_MQTT_BROKER_PORT = 1883
DEFAULT_MQTT_TOPIC = "IamAlive"
DEFAULT_READ_INTERVAL  = 5
# client_id = f'python-mqtt-{random.randint(0, 1000)}'


# mqtt callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK")
    else:
        print("Bad connection Returned code=", rc)


def on_publish(client, userdata, mid):
    print("mid: " + str(mid))


def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        C = (float(f.read()) / 1000)
        f.close()
        # print(f'The CPU temp in C is: {C}')
        return C

def get_disk_usage():
    values = {}
    BytesPerGB = 1024 * 1024 * 1024
    (total, used, free) = shutil.disk_usage("/")
    values["disk-total"] = ("%.2f" % (float(total)/BytesPerGB))
    values["disk-used"] = ("%.2f" % (float(used)/BytesPerGB))
    values["disk-free"] = ("%.2f" % (float(free)/BytesPerGB))
    return values
    
def get_hostname():
    hostname = socket.gethostname()
    return hostname

# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()

def set_id():
    id = 1
    return id


def main():
    parser = argparse.ArgumentParser(
        description="Publish enviroplus values over mqtt") 
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
    args = parser.parse_args()

    # Raspberry Pi ID
    hostname = get_hostname()
    device_serial_number = get_serial_number()
    device_id = "raspi-" + device_serial_number

    print(
        f"""test.py - Reads cpu temp and sends over mqtt.

    broker: {args.broker}
    client_id: {device_id}
    port: {args.port}
    topic: {args.topic}

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
            values = get_disk_usage()
            values["cpu_temp"] = get_cpu_temp()
            values["serial"] = device_serial_number
            values["hostname"] = hostname
            values["id"] = set_id()
            values["timestamp"] = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S") 
            print(values)
            mqtt_client.publish(args.topic, json.dumps(values))
            time.sleep(args.interval)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

