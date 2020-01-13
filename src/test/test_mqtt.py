import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    if json.loads(msg.payload.decode("utf-8")).get('data'):
        print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600)
client.subscribe('VideoCapture', qos=0)
client.loop_forever()