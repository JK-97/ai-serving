#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc

from google.protobuf.json_format import ParseDict


from interface import  reader_pb2_grpc as re_pb2_grpc
from interface import reader_pb2 as re_pb2

def TestStream(stub):
    load_info = {
        'source': "stream",
        'type': "real",
        'path': "rtsp://admin:jiangxing123@10.55.2.113:554/mpeg4/ch1/sub/"
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

def run():
    channel = grpc.insecure_channel("localhost:50051")
    re_stub = re_pb2_grpc.ReaderStub(channel)
    TestStream(re_stub)
    #TestImageSets(re_stub)
    #TestVideo(re_stub)




if __name__ == '__main__':
    run()
