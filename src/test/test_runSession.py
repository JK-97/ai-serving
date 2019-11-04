#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import uuid
from multiprocessing import Process

import cv2
import numpy as np
import redis
import requests

# PCS = 40
PCS = 1


def api_post(uid):
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data = {
        "uuid": uid,
        "path": "/Users/zhouyou/Desktop/pose.jpg"
    }
    result = requests.post("http://localhost:8080/api/v1alpha/detect", json.dumps(data))
    print("status code:", result.status_code)


def registry_redis(uid):
    r = redis.Redis(host="localhost", port=6379,db=5)
    v = None
    while v is None:
        v = r.get(uid)
    data = dict()
    data['data'] = json.loads((str(v, 'utf-8')))['data']
    cv2.imwrite("/tmp/tf_lite123.jpg", np.asarray(data['data']))
    print("success")


if __name__ == '__main__':
    uuid = str(uuid.uuid4())
    api_post(uuid)
    registry_redis(uuid)
