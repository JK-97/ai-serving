#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import grpc
import uuid
import time
import json
import redis

from PIL import Image
from io import BytesIO
from google.protobuf.json_format import ParseDict

from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc

def createAndLoadModel(stub):
    load_info = {
        'backend': {'impl': "rknn"},
        'model': {
            'implhash': "rknn",
            'version': "1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.CreateAndLoadModel(ParseDict(load_info, be_pb2.FullLoadRequest()))
    print("grpc.backend.createAndLoadModel >>>", response.code, response.msg)
    return response.msg


def listOne(stub, return_bid):
    backend_info = {'bid': return_bid}
    response = stub.ListBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
    print("grpc.backend.listBackend >>>",
          response.info,
          response.status,
          response.msg)
    return json.loads(response.status)["0"]


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
    print(v)



def run():
    channel = grpc.insecure_channel("localhost:50051")
    be_stub = be_pb2_grpc.BackendStub(channel)
    inf_stub = inf_pb2_grpc.InferenceStub(channel)
    start = time.time()
    ret = createAndLoadModel(be_stub)

    rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)

    status = 0
    while status != 4:
        status = listOne(be_stub, ret)
        time.sleep(1)
    end = time.time() 
    print("the time of vpmn create and load model is:%f"(end-start))
    inferLocal(inf_stub, ret, r)

if __name__ == '__main__':
    run()
