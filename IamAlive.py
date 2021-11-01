
import shutil
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json

from subprocess import PIPE, Popen, check_output
import time

broker = "10.0.0.5"
port = 1883
topic = "IamAlive"
interval = 5
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
    

# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()


def main():
    # Raspberry Pi ID
    device_serial_number = get_serial_number()
    device_id = "raspi-" + device_serial_number

    print(
        f"""test.py - Reads cpu temp and sends over mqtt.

    broker: {broker}
    client_id: {device_id}
    port: {port}
    topic: {topic}

    Press Ctrl+C to exit!

    """
    )

    mqtt_client = mqtt.Client(client_id=device_id)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.connect(broker, port=port)


    # Main loop to read data, display, and send over mqtt
    mqtt_client.loop_start()
    while True:
        try:
            values = get_disk_usage()
            values["cpu_temp"] = get_cpu_temp()
            values["serial"] = device_serial_number
            print(values)
            mqtt_client.publish(topic, json.dumps(values))
            time.sleep(interval)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

