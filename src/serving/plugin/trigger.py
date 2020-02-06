import logging
import cv2
import redis
import uuid
import json
import datetime
import base64
import paho.mqtt.client as mqtt

from PIL import ImageFile
from serving.core import inference
from serving.core import runtime


def drawFrame(points, frame):
    try:
        height, width, _ = frame.shape
        data = json.loads(str(points, 'utf-8'))
        red = (0, 0, 255)
        if len(data) != 0:
            for i, b in enumerate(data):
                x = int(b[2])
                y = int(b[3])
                wd = int(b[4])
                ht = int(b[5])
                left_x = 0 if x < 0 else x
                left_y = 0 if y < 0 else y
                right_x = width if x + wd > width else x + wd
                right_y = height if y + ht > height else y + ht
                text_left_y = 10 if left_y - 20 < 0 else left_y - 10
                cv2.rectangle(frame, (left_x, left_y), (right_x, right_y), red, 2)
                cv2.putText(frame, b[0], (left_x + 10, text_left_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red, 2)
        image_name = "/tmp/inference1.jpeg"
        cv2.imwrite(image_name, frame)
        f = open(image_name, 'rb')
        base64_data = base64.b64encode(f.read())
        b64str = base64_data.decode()
        now = datetime.datetime.now()
        mq_data = {"img": b64str, "data": data, "m": now.minute, "s": now.second}
        return mq_data
    except Exception as e:
        logging.exception(e)
        raise RuntimeError("failed to drawFrame")


def detectStream(r, client):
    try:
        while True:
            if "stream" in runtime.Images_pool.keys():
                frame = runtime.Images_pool["stream"]
                auuid = str(uuid.uuid4())
                data = {
                    "bid": "0",
                    "uuid": auuid,
                    "type": "stream",
                }
                inference.inferenceLocal(data)
                v = None
                while v is None:
                    v = r.get(auuid)
                    if v is not None and len(v):
                        mq_data = drawFrame(v, frame)
                        client.publish("VideoCapture", json.dumps(mq_data))
                    elif v is not None and not len(v):
                        mq_data = {"data": []}
                        client.publish("VideoCapture", json.dumps(mq_data))
                    else:
                        continue

                if json.loads(v.decode("utf-8")):
                    logging.debug(v)
    except Exception as e:
        logging.exception(e)
        raise RuntimeError("failed to detect stream")


def detectImageSets(r, client, type):
    try:
        mq_data = {}
        mq_lists = []
        while True:
            if runtime.ImageSets_info:
                auuid = str(uuid.uuid4())
                data = {
                    "bid": "0",
                    "uuid": auuid,
                    "type": "imageSets",
                }
                inference.inferenceLocal(data)
                image_id = runtime.ImageSets_info[0]
                frame = runtime.Images_pool[image_id]
                v = None
                while v is None:
                    v = r.get(auuid)
                    if type == 'real':
                        if v is not None and len(v):
                            mq_data = drawFrame(v, frame)
                            client.publish("VideoCapture", json.dumps(mq_data))
                        elif v is not None and not len(v):
                            mq_data = {"data": []}
                            client.publish("VideoCapture", json.dumps(mq_data))
                        else:
                            continue
                    else:
                        if v is not None and len(v):
                            mq_data = drawFrame(v, frame)
                        if v is not None and not len(v):
                            mq_data = {"data": []}
                        mq_lists.append(mq_data)

                del(runtime.Images_pool[image_id])
                del(runtime.ImageSets_info[0])
                if json.loads(v.decode("utf-8")):
                    logging.debug(v)
                if not runtime.ImageSets_info:
                    logging.debug("detect imagsSets ending")
                    if type != 'real':
                        client.publish("VideoCapture", json.dumps(mq_lists))
                    break
    except Exception as e:
        logging.exception(e)
        raise RuntimeError("failed to detect imageSets")


def trigger(data):
    rPool = redis.ConnectionPool(host="127.0.0.1", port=6379, db=5)
    r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)
    client = mqtt.Client()
    client.connect("127.0.0.1", 1883, 60)
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    if data.get("source") == "stream" or data.get("source") == "video":
        logging.debug("start detect stream or video")
        detectStream(r, client)

    if data.get("source") == "imageSets":
        logging.debug("start detect imageSets")
        detectImageSets(r, client, data.get('type'))







