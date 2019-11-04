import redis
import logging
import importlib
from serving import utils
from serving.backend import abstract_backend as ab
from serving.backend import supported_backend as sb
from settings import settings

BEs = {}
connection = {
    'redis.pool': redis.ConnectionPool(
                       host=utils.getKey('redis.host', dicts=settings),
                       port=utils.getKey('redis.port', dicts=settings),
                       db=5),
}
FGs = {
  'native_inference_stat': True
}
Ps = {}

def loadPlugins():
    Ps['encbase64'] = importlib.import_module('serving.plugin.encbase64')
    logging.debug("Loaded plugins: {}".format(Ps))


def createAndLoadModel(init_data):
    logging.debug("called createAndLoadBackends")
    bid = utils.getKey('bid', dicts=init_data, level=utils.Access.Optional)
    if bid is not None:
        return loadModel(init_data, bid)
    else:
        bid = createBackend(init_data)
        return loadModel(init_data, bid)

def createBackend(init_data):
    try:
        configs = {}
        configs['btype'] = utils.getKey('btype', dicts=init_data, v=sb.Validator)
        configs['version'] = utils.getKey('version', dicts=init_data)
        configs['storage'] = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
        configs['preheat'] = utils.getKey('preheat', dicts=settings)
        configs['queue.in'] = redis.Redis(connection_pool=connection['redis.pool'])

        new_backend = None
        if configs['btype'] == sb.Type.TfPy:
            from serving.backend import tensorflow_python as tfpy
            new_backend = tfpy.TfPyBackend(configs)

        if configs['btype'] == sb.Type.TfSrv:
            from serving.backend import tensorflow_serving as tfsrv
            configs['host'] = utils.getKey('be.tf.srv.host', dicts=settings)
            configs['port'] = utils.getKey('be.tf.srv.rest_port', dicts=settings)
            new_backend = tfsrv.TfSrvBackend(configs)

        if configs['btype'] == sb.Type.Torch:
            from serving.backend import torch_python as trpy
            configs['mixed_mode'] = utils.getKey('be.trpy.mixed_mode', dicts=settings),
            new_backend = trpy.TorchPyBackend(configs)

        if configs['btype'] == sb.Type.RknnPy:
            from serving.backend import rknn_python as rknnpy
            configs['target'] = utils.getKey('be.rknnpy.target', dicts=settings),
            new_backend = rknnpy.RKNNPyBackend(configs)

        if configs['btype'] == sb.Type.TfLite:
            from serving.backend import tensorflow_lite as tflite
            new_backend = tflite.TfLiteBackend(configs)

        bid = str(len(BEs))
        BEs[bid] = new_backend
        return bid
    except Exception as e:
        logging.exception(e)
        return ""

def loadModel(load_data, backend_id):
    backend = BEs.get(backend_id)
    if backend is not None:
        backend.run(load_data)
        return {'code': 0, 'msg': str(backend_id)}
    else:
        return {'code': 1, 'msg': "cannot find backend"}

@utils.gate(FGs['native_inference_stat'], lambda: print('IOI'))
def inferenceLocal(infer_data, backend_id):
    backend = BEs.get(backend_id)
    if backend is not None:
        backend.enqueueData(infer_data)
        return {'code': 0, 'msg': "enqueued"}
    else:
        return {'code': 1, 'msg': "cannot find backend"}

@utils.gate(FGs['native_inference_stat'], lambda: print('IOI'))
def inferenceRemote(infer_data, backend_id):
    backend = BEs.get(backend_id)
    if backend is not None:
        ret = Ps['encbase64'].to_image(infer_data['base64'],
                                           '/tmp/'+infer_data['uuid']+'.'+infer_data['type'])
        if ret['code'] != 0:
            return ret
        del infer_data['base64']
        infer_data['path'] = '/tmp/'+infer_data['uuid']+'.'+infer_data['type']
        backend.enqueueData(infer_data)
        return {'code': 0, 'msg': "enqueued"}
    else:
        return {'code': 1, 'msg': "cannot find backend"}

def listBackend(backend_id=""):
    backend = BEs.get(backend_id)
    if backend is not None:
         return backend.reportStatus()
    else:
        return {'model':"", 'status':"", 'msg':"cannot find backend"}

def terminateBackend(backend_id=""):
    backend = BEs.get(backend_id)
    if backend is not None:
        ret = backend.terminate()
        del BEs[backend_id]
        return ret
    else:
        return {'code':1, 'msg':"cannot find backend"}

