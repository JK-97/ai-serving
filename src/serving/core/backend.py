import logging
from serving import utils
from serving.core import runtime
from serving.core import regulator
from serving.backend import supported_backend as sb
from settings import settings
from serving.core.error_code import ExistBackendError, ReloadModelOnBackendError, TerminateBackendError, \
    CreateAndLoadModelError, FullHashValueError, ConstrainBackendInfoError,ListOneBackendError


def createAndLoadModelV2(info):
    fullhash = info['model']['fullhash']
    full = fullhash.split('-')
    if len(full) < 2:
        raise FullHashValueError(msg=FullHashValueError.msg)
    info['model']['implhash'] = full[0]
    info['model']['version'] = full[1]
    return createAndLoadModel(info)


def createAndLoadModel(info):
    createdBackendBid = None
    try:
        backend_request = parseValidBackendInfo(info['backend'])
        backend_instance = runtime.BEs.get(backend_request.get('bid'))
        if backend_instance is not None:
            logging.warning("called createAndLoadBackends, but give a bid, ignored")
            info['bid'] = backend_request['bid']
            return reloadModelOnBackend(info)
        else:
            model_request = {'implhash': info['model']['implhash'], 'version': info['model']['version']}
            ret = initializeBackend(backend_request, passby_model=model_request)
            createdBackendBid = ret['msg']
            info['bid'] = createdBackendBid
            return reloadModelOnBackend(info)
    except ExistBackendError as e:
        raise ExistBackendError(msg=repr(e))
    except ReloadModelOnBackendError as e:
        raise ReloadModelOnBackendError(msg=repr(e))
    except TerminateBackendError as e:
        raise TerminateBackendError(msg=repr(e))
    except ConstrainBackendInfoError as e:
        raise ConstrainBackendInfoError(msg=repr(e))
    except Exception as e:
        if createdBackendBid is not None:
            terminateBackend({'bid': createdBackendBid})
        raise CreateAndLoadModelError(msg=repr(e))


@utils.limit(runtime.FGs['enable_regulator'], regulator.CheckBackendExistInstance)
def initializeBackend(info, passby_model=None):
    configs = parseValidBackendInfo(info)
    # configs['queue.in'] = redis.Redis(connection_pool=runtime.Conns['redis.pool'])
    # TODO(arth): move to LoadModels
    # configs['encrypted'] = utils.getKey('encrypted', dicts=init_data)
    # if runtime.FGs['enable_sandbox']:
    #     configs['a64'] = utils.getKey('a64key', dicts=init_data, level=utils.Access.Optional)
    #     configs['pvt'] = utils.getKey('pvtpth', dicts=init_data, level=utils.Access.Optional)

    backend_instance = None
    impl_backend = utils.getKey('m', dicts={'m': str.split(configs['impl'], ".")[0]}, v=sb.Validator)

    if impl_backend == sb.Type.TfPy:
        from serving.backend import tensorflow_python as tfpy
        backend_instance = tfpy.TfPyBackend(configs)

    if impl_backend == sb.Type.TfSrv:
        from serving.backend import tensorflow_serving as tfsrv
        configs['host'] = utils.getKey('be.tf.srv.host', dicts=settings)
        configs['port'] = utils.getKey('be.tf.srv.rest_port', dicts=settings)
        backend_instance = tfsrv.TfSrvBackend(configs)

    if impl_backend == sb.Type.Torch:
        from serving.backend import torch_python as trpy
        configs['mixed_mode'] = utils.getKey('be.trpy.mixed_mode', dicts=settings),
        backend_instance = trpy.TorchPyBackend(configs)

    if impl_backend == sb.Type.RknnPy:
        from serving.backend import rknn_python as rknnpy
        configs['target'] = utils.getKey('be.rknnpy.target', dicts=settings),
        backend_instance = rknnpy.RKNNPyBackend(configs)

    if impl_backend == sb.Type.TfLite:
        from serving.backend import tensorflow_lite as tflite
        backend_instance = tflite.TfLiteBackend(configs)

    if backend_instance is None:
        raise CreateAndLoadModelError(msg="unknown error, failed to create backend")
    bid = str(len(runtime.BEs))
    runtime.BEs[bid] = backend_instance
    logging.debug(runtime.BEs)
    return {'code': 0, 'msg': bid}


def listAllBackends():
    status_list = []
    for key, _ in runtime.BEs.items():
        status_list.append(listOneBackend({'bid': key}))
    return {'backends': status_list}


def listOneBackend(info):
    backend_request = parseValidBackendInfo(info)
    backend_instance = runtime.BEs.get(backend_request['bid'])
    if backend_instance is None:
        raise ListOneBackendError(msg="failed to find backend")
    else:
        return backend_instance.reportStatus()


def reloadModelOnBackend(info):
    backend_request = parseValidBackendInfo(info)
    backend_instance = runtime.BEs.get(backend_request['bid'])
    if backend_instance is None:
        raise ReloadModelOnBackendError(msg="failed to find backend")
    else:
        backend_instance.run(info)
        return {'code': 0, 'msg': str(backend_request['bid'])}


def terminateBackend(info):
    backend_request = parseValidBackendInfo(info)
    backend_instance = runtime.BEs.get(backend_request['bid'])
    if backend_instance is None:
        raise TerminateBackendError(msg="failed to find backend")
    else:
        ret = backend_instance.terminate()
        del runtime.BEs[backend_request['bid']]
        return ret


def parseValidBackendInfo(info):
    temp_backend_info = info
    if temp_backend_info.get('storage') is None:
        temp_backend_info['storage'] = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    if temp_backend_info.get('preheat') is None:
        temp_backend_info['preheat'] = utils.getKey('preheat', dicts=settings)
    if temp_backend_info.get('batchsize') is None:
        temp_backend_info['batchsize'] = 1
    if temp_backend_info.get('inferprocnum') is None:
        temp_backend_info['inferprocnum'] = 1

    regulator.ConstrainBackendInfo(temp_backend_info)
    return temp_backend_info
