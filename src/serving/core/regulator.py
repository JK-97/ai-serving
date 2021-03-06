import json

from serving.core import runtime

from serving.core import backend
from serving.core.error_code import ConstrainBackendInfoError,LimitBackendError


def ConstrainBackendInfo(info):
    if info['batchsize'] > 1000:
        raise ConstrainBackendInfoError(msg="batchsize exceed limitation")
    if info['inferprocnum'] > 2:
        raise ConstrainBackendInfoError(msg="inference process number exceed limitation")


def CheckBackendExistInstance(info, passby_model):
    if passby_model is None:
        return False
    for key, _ in runtime.BEs.items():
        backendInfo = backend.listOneBackend({'bid': key})
        if int(json.loads(backendInfo['status'])["0"]) == 4 and backendInfo['info']['impl'] == info['impl'] \
                and backendInfo['model']['version'] == passby_model['version'] \
                and backendInfo['model']['implhash'] == passby_model['implhash']:
            return True
        else:
            backend.terminateBackend(info)


def LimitBackendInstance():
    if len(runtime.BEs) + 1 > 1:
        raise LimitBackendError(msg="backend instance exceed limitation")
