#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import sys
import time

import requests

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
    create_post_data['mtype'] = sys.argv[6]
    result = requests.post("http://localhost:8080/api/v1alpha/switch", data=json.dumps(create_post_data))
    return result


def reload_post():
    reload_post_data['bid'] = sys.argv[2]
    reload_post_data['model'] = sys.argv[3]
    reload_post_data['mode'] = sys.argv[4]
    reload_post_data['device'] = sys.argv[5]
    reload_post_data['mtype'] = sys.argv[6]
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
    result = get_status().json()
    print(result)
    if result['status']['0'] == 5:
        break
    time.sleep(1)
