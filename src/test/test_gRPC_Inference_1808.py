import grpc
import uuid
import time
import json
import redis
import base64

from PIL import Image
import cv2
import numpy as np
from io import BytesIO
from google.protobuf.json_format import ParseDict
from multiprocessing import Queue
import threading

from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import inference_pb2 as inf_pb2
from interface import inference_pb2_grpc as inf_pb2_grpc


q = Queue(maxsize = 1000)
pic_dict = {}

def createAndLoadModelV2(stub):
    load_info = {
        'backend': {'impl': "rknn", 'inferprocnum': 1},
        'model': {
            'fullhash': "31f312e631c2def1189b8c8d29e002e2-1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.CreateAndLoadModelV2(ParseDict(load_info, be_pb2.FullLoadRequestV2()))
    print("grpc.backend.createAndLoadModel >>>", response.code, response.msg)
    return response.msg


def listOne(stub, return_bid):
    backend_info = {'bid': return_bid}
    response = stub.ListBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
    print("grpc.backend.listBackend >>>",
          response.info,
          response.status,
          response.msg)
    return json.loads(response.status)["0"]


def get_frame():
    cap = cv2.VideoCapture(0)
    count = 0
    try:
        while True:
            ret, frame = cap.read()
            if (ret and (q.full() == False)):
                frame = Image.fromarray(frame)
                out_buffer = BytesIO()
                frame.save(out_buffer, format='JPEG')
                b64str = base64.b64encode(out_buffer.getvalue())

                # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # frame_encode = cv2.imencode('.jpg', frame)
                # str_encode = frame_encode[1].tostring()
                # out_buffer = BytesIO(str_encode)
                # b64str = base64.b64decode(out_buffer.getvalue())
                # print(len(out_buffer.getvalue()))
                # print(type(out_buffer.getvalue()))
                # print(len(b64str))

                auuid = str(count)
                pic_dict[auuid] = frame
                count += 1
                infer = {
                    'uuid': auuid,
                    'type': "jpg",
                    'base64': str(b64str, 'utf-8')
                }
                q.put(infer)
    except KeyboardInterrupt:
        cap.release()


def inferRemote(inf_stub, return_bid):
    try:
        while True:
            if not q.empty():
                infer = q.get()
                infer['bid'] = return_bid
                response = inf_stub.InferenceRemote(ParseDict(infer, inf_pb2.InferRequest()))
                time.sleep(0.1)
    except KeyboardInterrupt:
        exit(0)

def get_result(r1, r2, r3):
    count = 0
    l_used_time = []
    fps = 0
    try:
        while True:
            s = time.time()
            a = None
            b = None
            c = None
            result = None
            while (a is None and b is None and c is None):
                a = r1.get(str(count))
                b = r2.get(str(count))
                c = r3.get(str(count))
            frame = pic_dict[str(count)]
            pic_dict.pop(str(count))
            frame = np.array(frame)
            count += 1
            if a is not None:
                result = a
            if b is not None:
                result = b
            if c is not None:
                result = c
            result = result.decode(encoding='utf-8')
            result = json.loads(result)
            used_time = time.time() - s
            l_used_time.append(used_time)
            if len(l_used_time) > 20:
                l_used_time.pop(0)
            fps = int(1 / np.mean(l_used_time))
            for i in result:
                xmin = int(i[2])
                ymin = int(i[3])
                xmax = int(i[4])
                ymax = int(i[5])
                cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (0,0,255), 4)
                cv2.putText(frame, i[0], (xmin,ymin), cv2.FONT_HERSHEY_SIMPLEX, 1,  (0,0,255), 4, cv2.LINE_AA)
            cv2.putText(frame, str(fps), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 2,  (0,0,255), 4, cv2.LINE_AA)
            cv2.imshow('', frame)
            cv2.waitKey(1)
    except KeyboardInterrupt:
        exit(0)


def main():
    channel1 = grpc.insecure_channel("192.168.0.212:50051")
    channel2 = grpc.insecure_channel("192.168.0.213:50051")
    channel3 = grpc.insecure_channel("192.168.0.211:50051")
    be_stub1 = be_pb2_grpc.BackendStub(channel1)
    be_stub2 = be_pb2_grpc.BackendStub(channel2)
    be_stub3 = be_pb2_grpc.BackendStub(channel3)
    inf_stub1 = inf_pb2_grpc.InferenceStub(channel1)
    inf_stub2 = inf_pb2_grpc.InferenceStub(channel2)
    inf_stub3 = inf_pb2_grpc.InferenceStub(channel3)

    ret1 = createAndLoadModelV2(be_stub1)
    ret2 = createAndLoadModelV2(be_stub2)
    ret3 = createAndLoadModelV2(be_stub3)

    status1 = 0
    status2 = 0
    status3 = 0
    while (status1 != 4 and status2 != 4 and status3 != 4):
        status1 = listOne(be_stub1, ret1)
        status2 = listOne(be_stub2, ret2)
        status3 = listOne(be_stub3, ret3)
        time.sleep(1)

    rPool1 = redis.ConnectionPool(host="192.168.0.212", port=6379, db=5)
    r1 = redis.Redis(host="192.168.0.212", port=6379, connection_pool=rPool1)

    rPool2 = redis.ConnectionPool(host="192.168.0.213", port=6379, db=5)
    r2 = redis.Redis(host="192.168.0.213", port=6379, connection_pool=rPool2)

    rPool3 = redis.ConnectionPool(host="192.168.0.211", port=6379, db=5)
    r3 = redis.Redis(host="192.168.0.211", port=6379, connection_pool=rPool3)



    t_get_frame = threading.Thread(target=get_frame, args=())
    t_infer1 = threading.Thread(target=inferRemote, args=(inf_stub1, ret1))
    t_infer2 = threading.Thread(target=inferRemote, args=(inf_stub2, ret2))
    t_infer3 = threading.Thread(target=inferRemote, args=(inf_stub3, ret3))
    t_result = threading.Thread(target=get_result, args=(r1,r2, r3))

    try:
        t_get_frame.start()
        t_infer1.start()
        t_infer2.start()
        t_infer3.start()
        t_result.start()
    except KeyboardInterrupt:
        t_get_frame.terminate()
        t_infer1.terminate()
        t_infer2.terminate()
        t_infer3.terminate()
        t_result.terminate()

if __name__ == "__main__":
    main()





