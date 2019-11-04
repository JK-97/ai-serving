import json
import time
import uuid
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

r = redis.Redis(host="localhost", port=6379, db=5)


# detect pic

def detect_pic2():
    t = ThreadPoolExecutor(8)
    while True:
        ts = time.time()
        a = str(uuid.uuid4())
        t.submit(api_post, a, data_dic, 8080)
        print("a")
        v = None
        while v is None:
            v = r.get(a)
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['data']
        b = str(uuid.uuid4())
        t.submit(api_post, b, data, 8081)
        print("b")
        v = None
        while v is None:
            v = r.get(b)
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['data']
        c = str(uuid.uuid4())
        t.submit(api_post, c, data, 8082)
        print("c")
        v = None
        while v is None:
            v = r.get(c)
        data = dict()
        data['data'] = json.loads((str(v, 'utf-8')))['data']
        data['data'].append(data_dic['path'])
        d = str(uuid.uuid4())
        t.submit(api_post, d, data, 8083)
        print("d")
        v = None
        while v is None:
            v = r.get(d)
        print(v)
        te = time.time()
        print("total time::", str(te - ts))
        time.sleep(1)


detect_pic2()
