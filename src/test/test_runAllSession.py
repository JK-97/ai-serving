import json
import time
from concurrent.futures import ThreadPoolExecutor

import redis
import requests


def api_post(uid, data, port):
    """
    curl -X POST http://localhost:8080/api/v1alpha/detect -d '{"path": ""}'
    """
    data['uuid'] = uid
    requests.post("http://localhost:{}/api/v1alpha/detect".format(port), json.dumps(data))


th = {}
data_dic = {"path": "/Users/zhouyou/Documents/jx.github.com/jxserving-framework/src/mxNet/model1/jx_all.jpg"}

r = redis.Redis(host="localhost", port=6379)


# detect pic

def detect_pic2():
    t = ThreadPoolExecutor(8)
    while True:
        ts = time.time()
        t.submit(api_post, '1', data_dic, 8001)
        print("a")
        v = None
        while v is None:
            v = r.get('1')
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['result']
        t.submit(api_post, '2', data, 8002)
        print("b")

        v = None
        while v is None:
            v = r.get('2')
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['result']
        t.submit(api_post, '3', data, 8003)
        print("c")

        v = None
        while v is None:
            v = r.get('3')
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['result']
        data['data'].append(data_dic['path'])
        print("///", len(data['data']))
        t.submit(api_post, '4', data, 8004)
        print("d")
        v = None
        while v is None:
            v = r.get('4')
        print(v)
        te = time.time()
        print("total time::", str(te - ts))

        time.sleep(1)


detect_pic2()
