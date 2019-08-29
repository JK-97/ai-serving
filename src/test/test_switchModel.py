#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import time
import logging
import sys

def api_get():
    """
    curl -X GET http://localhost:8080/api/v1alpha/switch
    """
    result = requests.get("http://localhost:8080/api/v1alpha/switch")
    print(result.json())
    if result.json()['status'] == "loaded":
        return True
    return False



def api_post():
    """
    curl -X POST http://localhost:8080/api/v1alpha/switch -d '{"model": "example_model", "mode": "frozen", "preheat": "True"}'
    """
    data = {
        "model": sys.argv[1],
        "mode":  sys.argv[2],
        "device":  sys.argv[3],
        "preheat": True}
    result = requests.post("http://localhost:8080/api/v1alpha/switch", data=json.dumps(data))
    return result


response = None
try:
    response = api_post()
    print(response.json()['status'])
    print(type(response.json()))
except Exception as e:
    print(response.json())
    logging.critical(e)
    exit(-1)

while True:
    ret = api_get()
    if ret:
        exit(0)
    time.sleep(1)

