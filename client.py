import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    print("received message: " ,str(message.payload.decode("utf-8")))

mqttBroker ="10.0.0.5"

client = mqtt.Client("Smartphone")
client.connect(mqttBroker) 

client.loop_forever()

# client.subscribe([("IamAlive",1),("enviro",2)])
client.subscribe("IamAlive")
client.on_message=on_message 

# time.sleep(30)
# client.loop_stop()
