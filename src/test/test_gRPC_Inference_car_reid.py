#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
import uuid
import time
import json
import redis
import base64

import os
import numpy as np
from PIL import Image
from io import BytesIO
from google.protobuf.json_format import ParseDict
import multiprocessing
from multiprocessing import Queue, Process
import threading
from postpost import postpost
import pickle

from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc


def createAndLoadModelV2(stub):
    load_info = {
        'backend': {'impl': "rknn", 'inferprocnum': 1},
        'model': {
            'fullhash': "c20247ebc2ca1ab6c23e79c0acc83b58-1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.CreateAndLoadModelV2(ParseDict(load_info, be_pb2.FullLoadRequestV2()))
    print("grpc.backend.createAndLoadModel >>>", response.code, response.msg)
    return response.msg


def createAndLoadModelV3(stub):
    load_info = {
        'backend': {'impl': "traditional-generic.algorithmSingle", 'inferprocnum': 1},
        'model': {
            'fullhash': "6002149f66ad932d1fcfd059d23498d1-1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.CreateAndLoadModelV2(ParseDict(load_info, be_pb2.FullLoadRequestV2()))
    print("grpc.backend.createAndLoadModel >>>", response.code, response.msg)
    return response.msg


def createAndLoadModel(stub):
    load_info = {
        'backend': {'impl': "rknn"},
        'model': {
            'implhash': "31f312e631c2def1189b8c8d29e002e2",
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


test_image = "/home/ubuntu/Desktop/arthur/jxserving/pose.jpg"


def input_inference(inf_stub, return_bid):
    pic_path = '/home/ubuntu/Desktop/cheche/cheche/car'
    count = 0
    for n in range(12):
        old_img_paths = sorted(os.listdir(pic_path))
        for file in old_img_paths:
            if 125 * n <= int(file.split('.')[0]) < 125 * n + 25:
                if (int(file.split('.')[0]) % 2 - n % 2) == 0:
                    pic_name = os.path.join(pic_path, file)

                    infer = {
                        'bid': return_bid,
                        'uuid': str(count),
                        'path': pic_name
                    }
                    response = inf_stub.InferenceLocal(ParseDict(infer, inf_pb2.InferRequest()))
                    time.sleep(0.1)
                    count += 1


def inferLocal(inf_stub, return_bid1, return_bid2, r):

    input_pic1 = threading.Thread(target=input_inference, args=(inf_stub, return_bid1))
    input_pic1.start()
    time.sleep(1)

    s_time = time.time()
    try:
        count = 0
        pkl = []
        while True:
            res = []
            for i in range(13):
                uuid = str(count)
                v = None
                while v is None:
                    v = r.get(uuid)
                v = v.decode(encoding='utf-8')
                v = json.loads(v)
                res.append(v)
                count += 1
            print(count)

            pkl.append(res)

            if count == 156:
                break
        ori_h, ori_w = int(v[0][6]), int(v[0][7])
        extra_message = {
            'mask_path': '/home/ubuntu/Desktop/arthur/jxserving/src/test/m4.jpg',
            'original_shape': json.dumps([ori_h, ori_w]),
        }

        infer2 = {
            'bid': return_bid2,
            'uuid': 'fj',
            'path': json.dumps(pkl),
            'extra':  json.dumps(extra_message)
        }
        response = inf_stub.InferenceLocal(ParseDict(infer2, inf_pb2.InferRequest()))
        time.sleep(0.1)
        a = None
        while a is None:
            a = r.get('fj')
        a = a.decode(encoding='utf-8')
        print(a)

        e_time = time.time()
        print("infer time:", e_time-s_time)
    except KeyboardInterrupt:
        time.sleep(5)
        input_pic1.terminate()
        print("ctrl + c, exit main!")


def inferRemote(inf_stub, return_bid, r):
    img = Image.open(test_image)
    out_buffer = BytesIO()
    img.save(out_buffer, format='JPEG')
    b64str = base64.b64encode(out_buffer.getvalue())

    auuid = str(uuid.uuid4())
    infer = {
        'bid': return_bid,
        'uuid': auuid,
        'type': "jpg",
        'base64': str(b64str, 'utf-8'),
    }
    response = inf_stub.InferenceRemote(ParseDict(infer, inf_pb2.InferRequest()))
    print("grpc.inference.inferenceRemote >>>", response.code, response.msg)
    v = None
    while v is None:
        v = r.get(auuid)
    print(v)


def run():
    channel = grpc.insecure_channel("localhost:50051")
    be_stub = be_pb2_grpc.BackendStub(channel)
    inf_stub = inf_pb2_grpc.InferenceStub(channel)

    ret = createAndLoadModelV2(be_stub)

    status = 0
    while status != 4:
        status = listOne(be_stub, ret)
        time.sleep(1)

    ret2 = createAndLoadModelV3(be_stub)

    status = 0
    while status != 4:
        status = listOne(be_stub, ret)
        time.sleep(1)

    rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)

    inferLocal(inf_stub, ret, ret2, r)
   # inferRemote(inf_stub, ret, r)


if __name__ == '__main__':
    run()
