#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
import paho.mqtt.client as mqtt
import json

from google.protobuf.json_format import ParseDict


from interface import  reader_pb2_grpc as re_pb2_grpc
from interface import reader_pb2 as re_pb2

def TestStream(stub):
    load_info = {
        'source': "stream",
        'type': "real",
        'path': "rtmp://10.55.5.74/live/usb0"
    }
    response = stub.GetReader(ParseDict(load_info, re_pb2.ReadRequest()))
    print("grpc.Reader >>>", response.code, response.msg)


def TestImageSets(stub):
    load_info = {
        'source': "imageSets",
        'type': "real",
        'path': "http://10.55.5.11/data/testset.zip",
    }
    response = stub.GetReader(ParseDict(load_info, re_pb2.ReadRequest()))
    print("grpc.Reader >>>", response.code, response.msg)


def TestVideo(stub):
    load_info = {
        'source': "video",
        'type': "real",
        'path': "/data/video.tar",
    }
    response = stub.GetReader(ParseDict(load_info, re_pb2.ReadRequest()))
    print("grpc.Reader >>>", response.code, response.msg)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    if json.loads(msg.payload.decode("utf-8")).get('data'):
        print(msg.topic + " " + str(msg.payload))


def run():
    channel = grpc.insecure_channel("localhost:50051")
    re_stub = re_pb2_grpc.ReaderStub(channel)

    #TestStream(re_stub)
    TestImageSets(re_stub)
    #TestVideo(re_stub)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect('127.0.0.1', 1883, 600)
    client.subscribe('VideoCapture', qos=0)
    client.loop_forever()


if __name__ == '__main__':
    run()
