#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import sys
import time

import requests


def api_get(port):
    """
    curl -X GET http://localhost:8080/api/v1alpha/switch
    """
    result = requests.get("http://localhost:{}/api/v1alpha/switch".format(port))
    print(result.json())
    return result.json()['status']['0']


def api_post2(model, type, port):
    """
    curl -X POST http://localhost:8080/api/v1alpha/switch -d '{"mxNet": "example_model", "mode": "frozen", "preheat": "True"}'
    """
    print("switch model -->>>", model, '---.>>>>', type)
    data = {
        'btype': "mxNet",
        "model": model,
        "mode": "frozen",
        "device": "sd",
        "mtype": type,
        "preheat": True
    }
    url = "http://localhost:{}/api/v1alpha/switch".format(port)
    result = requests.post(url, data=json.dumps(data))
    return result


# 加载模型 1 2 3 4
model_num = 4


def load_model():
    for i in range(0, model_num):
        model_name = "model" + str(i + 1)
        port = 8080 + i
        api_post2(model_name, i, port)
        while True:
            ret = api_get(port)
            if ret == 5:
                print("\nload model{} succ \n".format(i))
                break
            elif ret == 1:
                print("\nload model{} failed \n".format(i))
                break
            time.sleep(0.05)


load_model()
