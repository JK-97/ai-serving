import logging
from serving import utils
from serving.core import queue as q
from serving.backend import abstract_backend as ab
from settings import settings

BACKEND = None
BEs = {}

class ErrorMessage():
    def __init__(backend_id, brief, message):
        self.backend_id = backend_id
        self.brief = brief
        self.message = message


def createBackends(threads_num = 1):
    for i in range(0, threads_num):
        BEs[i] = newBackendWithCollection(utils.getKey('collection_path', dicts=settings,
                                                      env_key='JXSRV_COLLECTION_PATH'))

def loadBackends(load_data, backend_id=0):
    logging.debug("{}({}) to loadModel".format(backend_id, BEs[backend_id]))
    BEs[backend_id].initBackend(load_data)

def inputData(infer_data, backend_id=0):
    BEs[backend_id].importer(infer_data)
    #return q.output_queue.get()
    return {'see': "out"}

def reporter(backend_id=0):
    logging.debug("backend: {}({})".format(backend_id, BEs[backend_id]))
    return BEs[backend_id].reportStatus()

def newBackendWithCollection(collection):
    backend_type = utils.getKey('backend', dicts=settings,
                          env_key='JXSRV_BACKEND', v=ab.BackendValidator)

    if backend_type == ab.Type.TfPy:
        from serving.backend import tensorflow_python as tfpy
        return tfpy.TfPyBackend(collection, {
            'preheat': utils.getKey('be.tfpy.preheat', dicts=settings),
            'redis.host': utils.getKey('redis.host', dicts=settings),
            'redis.port': utils.getKey('redis.port', dicts=settings),
        })
    if backend_type == ab.Type.TfSrv:
        from serving.backend import tensorflow_serving as tfsrv
        return tfsrv.TfSrvBackend(collection, {
            'host': utils.getKey('be.tfsrv.host', dicts=settings),
            'port': utils.getKey('be.tfsrv.rest_port', dicts=settings),
            'preheat': utils.getKey('be.tfsrv.preheat', dicts=settings),
            'redis.host': utils.getKey('redis.host', dicts=settings),
            'redis.port': utils.getKey('redis.port', dicts=settings),
        })
    if backend_type == ab.Type.Torch:
        from serving.backend import torch_python as trpy
        return trpy.TorchPyBackend(collection, {
            'preheat': utils.getKey('be.trpy.preheat', dicts=settings),
            'mixed_mode': utils.getKey('be.trpy.mixed_mode', dicts=settings),
            'redis.host': utils.getKey('redis.host', dicts=settings),
            'redis.port': utils.getKey('redis.port', dicts=settings),
        })
    if backend_type == ab.Type.RknnPy:
        from serving.backend import rknn_python as rknnpy
        return rknnpy.RKNNPyBackend(collection, {
            'preheat': utils.getKey('be.rknnpy.preheat', dicts=settings),
            'target': utils.getKey('be.rknnpy.target', dicts=settings),
            'redis.host': utils.getKey('redis.host', dicts=settings),
            'redis.port': utils.getKey('redis.port', dicts=settings),
        })

