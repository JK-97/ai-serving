#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
import uuid
import time
import json
import redis
import base64

from PIL import Image
from io import BytesIO

from interface import common_pb2 as c_pb2
from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    be_stub = be_pb2_grpc.BackendStub(channel)
    inf_stub = inf_pb2_grpc.InferenceStub(channel)

    # CreateAndLoadModel
    response = inf_stub.CreateAndLoadModel(inf_pb2.LoadRequest(
        bid="",
        btype="tensorflow",
        model="tfpy_frozen_ver",
        version="1",
        mode="frozen",
        extra="",
    ))
    print("grpc.inference.createAndLoadModel >>>", response.code, response.msg)
    return_bid = response.msg

    status = 0
    while status != 4:
        response = be_stub.ListBackend(be_pb2.BackendRequest(bid=return_bid, btype=""))
        print("grpc.backend.listBackend >>>",
            response.bid,
            response.model,
            response.status,
            response.msg)
        status = json.loads(response.status)["0"]
        time.sleep(1)

    # ReloadModel
    response = inf_stub.ReloadModel(inf_pb2.LoadRequest(
        bid=return_bid,
        btype="",
        model="tfpy_frozen_ver",
        version="1",
        mode="frozen",
        extra="",
    ))
    print("grpc.backend.reloadModel >>>", response.code, response.msg)

    status = 0
    while status != 4:
        response = be_stub.ListBackend(be_pb2.BackendRequest(bid=return_bid, btype=""))
        print("grpc.backend.listBackend >>>",
            response.bid,
            response.model,
            response.status,
            response.msg)
        status = json.loads(response.status)["0"]
        time.sleep(1)

    rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)

    # InferenceLocal
    auuid = str(uuid.uuid4())
    response = inf_stub.InferenceLocal(inf_pb2.InferRequest(
        bid=return_bid,
        uuid=auuid,
        path="/home/ubuntu/ar_example_model/preheat.jpeg",
        type="",
        base64="",
    ))
    print("grpc.inference.inferenceLocal >>>", response.code, response.msg)
    v = None
    while v is None:
        v = r.get(auuid)
    print(v)

    # InferenceRemote
    img = Image.open("/home/ubuntu/ar_example_model/preheat.jpeg")
    out_buffer = BytesIO()
    img.save(out_buffer, format='JPEG')
    b64str = base64.b64encode(out_buffer.getvalue())
    auuid = str(uuid.uuid4())
    response = inf_stub.InferenceRemote(inf_pb2.InferRequest(
        bid=return_bid,
        uuid=auuid,
        path="",
        type="jpeg",
        base64=str(b64str, 'utf-8'),
    ))
    print("grpc.inference.inferenceRemote >>>", response.code, response.msg)
    v = None
    while v is None:
        v = r.get(auuid)
    print(v)


if __name__ == '__main__':
    run()

