#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import time
from multiprocessing import Process
import numpy as np
import redis
import uuid

#PCS = 40
PCS = 1

def api_post(uid):
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data = {
        "uuid": uid,
        "path": "/home/ubuntu/ar_example_model/preheat.jpeg"}
    #data = {"path": "/home/jiangxing/ar_example_model/ar_pose/data/preview.jpg"}
    #result = requests.post("http://localhost:8080/api/v1alpha/detect", data=json.dumps(data))
    p = Process(target=requests.post, args=("http://localhost:8080/api/v1alpha/detect", json.dumps(data)))
    return p
    """
    while True:
        p = Process(target=requests.post, args=("http://localhost:8080/api/v1alpha/detect", json.dumps(data)))
        p.start()
        time.sleep(0.04)
    """

# api_post_image()
th = {}
for i in range (0, PCS):
    print(i)
    th[i] = str(uuid.uuid4())
    p = api_post(th[i])
    p.start()

"""
for i in range (0, PCS):
    th[i].start()

for i in range (0, PCS):
    th[i].join()
"""

"""
det = []
for i in range (0, PCS):
    t1 = time.time()
    th[i].join()
    t2 = time.time()
    det.append(t2-t1)
    if len(det) > 20:
        det.pop(0)
    fps = 1/np.mean(det)
    print(fps)

#print(PCS/(t2-t1))
"""

r = redis.Redis(host="localhost", port=6379)
while True:
    count = 0
    for i in range (0, PCS):
        v = r.get(th[i])
        if v != None:
            count = count+1
            print(i, v)
    if count == PCS:
        break
