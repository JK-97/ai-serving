import logging

import psutil

from serving import utils
from serving.backend import supported_backend as sb
from settings import settings

BEs = {}


class ErrorMessage():
    def __init__(self, backend_id, brief, message):
        self.backend_id = backend_id
        self.brief = brief
        self.message = message


def cpu_info():
    return psutil.cpu_percent(interval=1)


def memory_info():
    return psutil.virtual_memory().percent


# [ATTENTION] these functions are very fragile, many vars haven't been validated
def createAndLoadBackends(init_data):
    logging.debug("called createAndLoadBackends")
    bid = utils.getKey('bid', dicts=init_data, level=utils.Access.Optional)
    if bid is not None:
        return loadBackends(init_data, bid)
    else:
        bid = len(BEs)
        BEs[bid] = createBackends(init_data)
        return loadBackends(init_data, bid)


def loadBackends(load_data, backend_id=0):
    backend = BEs.get(backend_id)
    if backend is not None:
        backend.initBackend(load_data)
        return {"status": "succ", "bid": str(backend_id)}
    else:
        return {"status": "failed", "msg": "cannot find backend"}


def inputData(infer_data, backend_id=0):
    BEs[backend_id].enqueueData(infer_data)
    return {'status': "succ"}


def reporter(backend_id=0):
    backend = BEs.get(backend_id)
    if backend is not None:
        return backend.reportStatus()
    else:
        return {"status": "failed", "msg": "cannot find backend"}


def createBackends(init_data):
    configs = {}
    configs['btype'] = utils.getKey('btype', dicts=init_data, v=sb.Validator)
    configs['mtype'] = utils.getKey('mtype', dicts=settings)
    configs['storage'] = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    configs['preheat'] = utils.getKey('preheat', dicts=settings)
    configs['redis.host'] = utils.getKey('redis.host', dicts=settings)
    configs['redis.port'] = utils.getKey('redis.port', dicts=settings)

    if configs['btype'] == sb.Type.TfPy:
        from serving.backend import tensorflow_python as tfpy
        return tfpy.TfPyBackend(configs)

    if configs['btype'] == sb.Type.TfSrv:
        from serving.backend import tensorflow_serving as tfsrv
        configs['host'] = utils.getKey('be.tf.srv.host', dicts=settings)
        configs['port'] = utils.getKey('be.tf.srv.rest_port', dicts=settings)
        return tfsrv.TfSrvBackend(configs)

    if configs['btype'] == sb.Type.Torch:
        from serving.backend import torch_python as trpy
        configs['mixed_mode'] = utils.getKey('be.trpy.mixed_mode', dicts=settings),
        return trpy.TorchPyBackend(configs)

    if configs['btype'] == sb.Type.RknnPy:
        from serving.backend import rknn_python as rknnpy
        configs['target'] = utils.getKey('be.rknnpy.target', dicts=settings),
        return rknnpy.RKNNPyBackend(configs)

    if configs['btype'] == sb.Type.TfLite:
        from serving.backend import tensorflow_lite as tflite
        return tflite.TfLiteBackend(configs)

    if configs['btype'] == sb.Type.MxNet:
        from serving.backend import mxnet_python as tmxNet
        return tmxNet.MxNetBackend(configs)
