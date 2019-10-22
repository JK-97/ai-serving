#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
from multiprocessing import Process

import requests

# PCS = 40
PCS = 1


def api_post(uid):
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data = {
        "uuid": uid,
        "path": "/Users/zhouyou/Documents/jx.github.com/jxserving/src/model/model1/jx_all.jpg"
    }
    while True:
        p = Process(target=requests.post, args=("http://localhost:8080/api/v1alpha/detect", json.dumps(data)))
        p.start()
        time.sleep(0.04)


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
