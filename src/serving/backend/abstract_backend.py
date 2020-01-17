"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import sys
import json
import redis
import signal
import logging
import importlib
from enum import Enum, unique
from multiprocessing import Process, Value

from serving import utils
from serving.core import model
from serving.core import runtime
from serving.core import sandbox


@unique
class Status(Enum):
    Unloaded = 0
    Cleaning = 1
    Loading = 2
    Preheating = 3
    Running = 4
    Exited = 5
    Error = 6
    Error_labels = 7


@unique
class State(Enum):
    Initializing = 0
    Initialized = 1
    Cleaning = 2
    Cleaned = 3
    Loading = 4
    Loaded = 5
    Running = 6
    Exiting = 7
    Exited = 8
    Error = 9


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, configurations={}):
        self.state = Value('h', State.Initializing.value)
        self.backend_configs = configurations
        self.model_configs = {
            'implhash': "",
            'version': "",
            'disthash': "",
        }

        self.model_path = ""
        self.model_filename = "model_core"

        self.configs = {}
        self.configs['queue.in'] = redis.Redis(connection_pool=runtime.Conns['redis.pool'])

        self.inferproc_th = [None] * self.backend_configs['inferprocnum']
        self.inferproc_state = [Value('B', Status.Unloaded.value)] * self.backend_configs['inferprocnum']

        self.model_object = None
        self.predp = None
        self.postdp = None
        # self.state.value = State.Initialized.value

    @utils.gate(runtime.FGs['enable_device_validation'], runtime.default_dev_validator)
    def run(self, switch_configs):
        try:
            if not runtime.FGs['enable_sandbox'] and bool(utils.getKey('encrypted', dicts=switch_configs)):
                self.state.value = State.Error.value
                raise RuntimeError("model is encrypted, but sandbox is not available")

            # cleaning state
            self.state.value = State.Cleaning.value
            target_model = utils.getKey('model', dicts=switch_configs)
            target_implhash = target_model.get('implhash')
            target_version = target_model.get('version')
            if target_implhash is None:
                target_implhash = model.generateModelImplHashByExtractInfo(target_model)
            target_model_config = model.loadModelInfoFromStorage(target_implhash, target_version)
            for i in range(self.backend_configs['inferprocnum']):
                if self.inferproc_th[i] is not None:
                    self.inferproc_th[i].terminate()
                    logging.debug("th: >>> {} is terminated".format(i))
            self.state.value = State.Cleaned.value

            # loading state
            self.state.value = State.Loading.value
            self.model_configs = target_model_config
            self.model_path = os.path.join(self.backend_configs['storage'], "models", target_implhash, target_version)

            # load customized model pre-process and post-process functions
            sys.path.append(self.model_path)
            self.predp = importlib.import_module('pre_dataprocess')
            self.postdp = importlib.import_module('post_dataprocess')
            self.predp = importlib.reload(self.predp)
            self.postdp = importlib.reload(self.postdp)
            self.state.value = State.Loaded.value
            sys.path.remove(self.model_path)

            # start inference process
            for i in range(self.backend_configs['inferprocnum']):
                self.inferproc_th[i] = Process(
                    target=self.predictor,
                    args=(switch_configs,
                          self.inferproc_state[i], self.state,))
                self.inferproc_th[i].start()
            self.state.value = State.Running.value
        except Exception as e:
            self.state.value = State.Error.value
            raise e

    # NOTICED: the following function will be ran as a independent process
    @utils.gate(runtime.FGs['enable_device_validation'], runtime.default_dev_validator)
    def predictor(self, switch_configs, load_status, state):
        try:
            # loading model object
            load_status.value = Status.Loading.value
            is_loaded_param = False
            if runtime.FGs['enable_sandbox'] and bool(switch_configs.get('encrypted')):
                key = sandbox.sha256_recover(switch_configs['a64key'], switch_configs['pvtkey'])
                sandbox._decrypt(key,
                                 os.path.join(self.model_path, self.model_filename),
                                 os.path.join(self.model_path, "model_dore"))
                self.model_filename = "model_dore"
                try:
                    # TODO(): still exist leaking risks
                    is_loaded_param = self._loadModel(switch_configs)
                except Exception as e:
                    os.remove(os.path.join(self.model_path, self.model_filename))
                    raise e
                os.remove(os.path.join(self.model_path, self.model_filename))
            else:
                logging.warning("loaded a model WITHOUT encryption")
                self.model_filename = "model_dore"
                is_loaded_param = self._loadModel(switch_configs)
            assert self.model_object is not None
            if not is_loaded_param:
                self._loadParameter(switch_configs)
            # preheat
            worker_queue_id = self.model_configs['implhash'] + self.model_configs['version']
            if self.backend_configs.get('preheat') is not None:
                load_status.value = Status.Preheating.value
                self.enqueueData({'uuid': "preheat", 'path': self.backend_configs['preheat']})
                logging.debug("preheating _inferData")
                self._inferData(worker_queue_id, 1)
                logging.debug("preheated _inferData")

            # predicting loop
            load_status.value = Status.Running.value
            while True:
                if self.state.value == State.Exiting.value:
                    break
                id_lists, result_lists = self._inferData(worker_queue_id, self.backend_configs['batchsize'])
                for i in range(self.backend_configs['batchsize']):
                    self.configs['queue.in'].set(id_lists[i], json.dumps(result_lists[i]))
            load_status.value = Status.Exited.value
        except Exception as e:
            rknn_err_msg = "RKNN_ERR_DEVICE_UNAVAILABLE"
            if rknn_err_msg in repr(e):
                os.kill(runtime.main_process_pid, signal.SIGTERM)
            if runtime.dev_debug:
                logging.exception(e)
            else:
                logging.error(e)
            load_status.value = Status.Cleaning.value
            if isinstance(e, ValueError):
                load_status.value = Status.Error_labels.value
            else:
                load_status.value = Status.Error.value
            self.model_object = None

    def enqueueData(self, infer_data, queue_id=None):
        if queue_id is None:
            queue_id = self.model_configs['implhash'] + self.model_configs['version']
        self.configs['queue.in'].rpush(queue_id, json.dumps(infer_data))

    def reportStatus(self):
        status_vector = {'state': self.state.value}
        if self.state.value >= State.Loading.value:
            for i in range(0, self.backend_configs['inferprocnum']):
                status_vector[str(i)] = self.inferproc_state[i].value
        return {
            'info': self.backend_configs,
            'status': json.dumps(status_vector),
            'msg': "",
            'model': self.model_configs
        }

    def terminate(self):
        procnum = self.backend_configs['inferprocnum']
        for i in range(procnum):
            if self.inferproc_th[i] is not None:
                self.inferproc_th[i].terminate()

    @abc.abstractmethod
    def _loadModel(self, load_configs):
        raise NotImplementedError()

    @abc.abstractmethod
    def _loadParameter(self, load_configs):
        raise NotImplementedError()

    @abc.abstractmethod
    def _inferData(self, infer_data, batchsize):
        raise NotImplementedError()
