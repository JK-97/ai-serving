#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import grpc
import uuid
import time
import json
import redis
import psutil 

from PIL import Image
from io import BytesIO
from google.protobuf.json_format import ParseDict

from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc

def createAndLoadModel(stub):
    load_info = {
        'backend': {'impl': "tensorflow.frozen"},
        'model': {
            'implhash': "226a7354795692913f24bee21b0cd387",
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
    tmp = os.popen("ps -ef |grep redis-server |head -n 1 |awk '{print $2}'").readlines()
    redis_pid = int(tmp[0][:-1])
    p = psutil.Process(redis_pid)
    print('redis初始的资源占用情况:')   
    print('运行状态:', p.status())        
    print('CPU信息:',  p.cpu_times())     
    print('内存信息:', p.memory_percent())
    print('内存使用:', p.memory_info())   
    print('IO信息：', p.io_counters() )   
    print('线程数：', p.num_threads() ) 
    channel = grpc.insecure_channel("localhost:50051")
    be_stub = be_pb2_grpc.BackendStub(channel)
    inf_stub = inf_pb2_grpc.InferenceStub(channel)

    ret = createAndLoadModel(be_stub)

    rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)

    status = 0
    while status != 4:
        status = listOne(be_stub, ret)
        time.sleep(1)

    inferLocal(inf_stub, ret, r)
    p = psutil.Process(redis_pid)
    print('进行inferlocal后redis的资源占用情况:')
    print('运行状态:', p.status())        
    print('CPU信息:',  p.cpu_times())     
    print('内存信息:', p.memory_percent())
    print('内存使用:', p.memory_info())   
    print('IO信息：', p.io_counters() )   
    print('线程数：', p.num_threads() )   

if __name__ == '__main__':
    run()
