#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import grpc
import uuid
import time
import json
import redis

from google.protobuf.json_format import ParseDict

from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc

test_image = "/home/hebi/test.jpg"

def inferLocal(inf_stub, return_bid, r):
    auuid = str(uuid.uuid4())
    infer = {
        'bid': return_bid,
        'uuid': auuid,
        'path': test_image,
    }
    response = inf_stub.InferenceLocal(ParseDict(infer, inf_pb2.InferRequest()))
    print("grpc.inference.inferenceLocal >>>", response.code, response.msg)
    v = None
    while v is None:
        v = r.get(auuid)
    print("call result is:", v)



def run():
    channel = grpc.insecure_channel("localhost:50051")
    inf_stub = inf_pb2_grpc.InferenceStub(channel)
    rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)
    ret = "0"
    inferLocal(inf_stub, ret, r)

if __name__ == '__main__':
    run()
