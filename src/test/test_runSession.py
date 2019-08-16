#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

def api_post():
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data = {"path": "/home/tx1-node1/ai-demo/jxserving/src/preheat/preheat.jpeg"}
    result = requests.post("http://localhost:8080/api/v1alpha/detect", data=json.dumps(data))
    print(result.json()['result'])
    print(type(result.json()))

# api_post_image()
api_post()

