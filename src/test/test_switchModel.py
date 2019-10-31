#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import time
import logging
import sys

create_post_data = {
  'btype': "tensorflow",
  'model': "",
  'mode': "",
  'device': "",
  'preheat': True,
}

reload_post_data = {
  'bid': 0,
  'model': "",
  'mode': "",
  'device': "",
  'preheat': True,
}

def get_status():
    return requests.get("http://localhost:8080/api/v1alpha/switch")

def create_post():
    create_post_data['btype'] = sys.argv[2]
    create_post_data['model'] = sys.argv[3]
    create_post_data['mode'] = sys.argv[4]
    create_post_data['device'] = sys.argv[5]
    result = requests.post("http://localhost:8080/api/v1alpha/switch", data=json.dumps(create_post_data))
    return result

def reload_post():
    reload_post_data['bid'] = sys.argv[2]
    reload_post_data['model'] = sys.argv[3]
    reload_post_data['mode'] = sys.argv[4]
    reload_post_data['device'] = sys.argv[5]
    result = requests.post("http://localhost:8080/api/v1alpha/switch", data=json.dumps(reload_post_data))
    return result


if sys.argv[1] == "create":
    try:
        print(create_post().json())
    except Exception as e:
        logging.critical(e)
        exit(-1)

if sys.argv[1] == "reload":
    try:
        print(reload_post().json())
    except Exception as e:
        logging.critical(e)
        exit(-1)

while True:
    print(get_status().json())
    time.sleep(1)

