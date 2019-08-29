#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

def api_post():
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data = {"path": "/home/jiangxing/ar_example_model/preheat.jpeg"}
    #data = {"path": "/home/jiangxing/ar_example_model/ar_pose/data/preview.jpg"}
    result = requests.post("http://localhost:8080/api/v1alpha/detect", data=json.dumps(data))
    print(result.json())

# api_post_image()
api_post()

