"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import sys
import rsa
import logging
import binascii
import importlib
import rapidjson as json
from enum import Enum, unique
from multiprocessing import Process, Value
from serving import utils
from serving.core import runtime
from serving.core import sandbox


@unique
class Status(Enum):
    Unloaded   = 0
    Cleaning   = 1
    Loading    = 2
    Preheating = 3
    Running    = 4
    Exited     = 5
    Error      = 6


@unique
class State(Enum):
    Initializing  = 0
    Initialized   = 1
    Cleaning      = 2
    Cleaned       = 3
    Loading       = 4
    Loaded        = 5
    Running       = 6
    Exiting       = 7
    Exited        = 8
    Error         = 9


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, configurations = {}):
        self.state = Value('h', State.Initializing.value)

        self.configs = configurations # inc: btype, storage, preheat, queue.in
        self.configs['model_name'] = ""
        self.configs['model_path'] = ""
        self.configs['version'] = ""
        self.configs['labels'] = []
        self.configs['threshold'] = {}
        self.configs['batchsize'] = 1

        self.configs['inferproc_num'] = 1
        self.inferproc_th = [None] * self.configs['inferproc_num']
        self.inferproc_state = [Value('B', Status.Unloaded.value)] * self.configs['inferproc_num']

        self.model_object = None
        self.predp = None
        self.postdp = None

        self.state.value = State.Initialized.value

    @utils.gate(runtime.FGs['enable_device_validation'], runtime.default_dev_validator)
    def run(self, switch_configs):
        try:
            if not runtime.FGs['enable_sandbox'] and bool(utils.getKey('encrypted', dicts=switch_configs)):
                raise RuntimeError("model is encrypted, but sandbox is not available")
            self.state.value = State.Cleaning.value
            target_model = utils.getKey('model', dicts=switch_configs)
            target_version = utils.getKey('version', dicts=switch_configs)
            if self.configs['model_name'] == target_model and self.configs['version'] == target_version:
                self.state.value = State.Running.value
                return {'code': 0, 'msg': "reload as a same model"}
            for i in range(self.configs['inferproc_num']):
                if self.inferproc_th[i] is not None:
                    logging.debug("th: >>>", i, "terminated")
                    self.inferproc_th[i].terminate()
            self.state.value = State.Cleaned.value

            self.state.value = State.Loading.value
            self.configs['model_name'] = target_model
            self.configs['version'] = target_version
            # validate model path
            self.configs['model_path'] = os.path.join(
                self.configs['storage'],
                "models",
                self.configs['model_name'],
                self.configs['version'])
            if not os.path.isdir(self.configs['model_path']):
                raise RuntimeError("model does not exist: {}".format(self.configs['model_path']))
            # load customized model pre-process and post-process functions
            sys.path.append(self.configs['model_path'])
            self.predp = importlib.import_module('pre_dataprocess')
            self.postdp = importlib.import_module('post_dataprocess')
            # load extra configurations
            with open(os.path.join(self.configs['model_path'], 'distros.json')) as distro_file:
                self.configs['model_configs'] = self.loadData(distro_file.read())
            self.state.value = State.Loaded.value

            # start process
            for i in range(self.configs['inferproc_num']):
                self.inferproc_th[i] = Process(
                    target=self.predictor,
                    args=(switch_configs,
                        self.inferproc_state[i], self.state,))
                self.inferproc_th[i].start()
            self.state.value = State.Running.value
        except Exception as e:
            self.state.value = State.Error.value
            logging.exception(e)
            return {'code': 1, 'msg': "an exception raised"}

    @utils.gate(runtime.FGs['enable_device_validation'], runtime.default_dev_validator)
    def predictor(self, switch_configs, load_status, state):
        try:
            # loading model object
            load_status.value = Status.Loading.value
            is_loaded_param = False
            if runtime.FGs['enable_sandbox'] and bool(utils.getKey('encrypted', dicts=switch_configs)):
                key = sandbox.sha256_recover(self.configs['a64'], self.configs['pvt'])
                sandbox._decrypt(key,
                    os.path.join(self.configs['model_path'], "model_core"),
                    os.path.join(self.configs['model_path'], "model_dore"))
                self.configs['model_filename'] = "model_dore"
                is_loaded_param = self._loadModel(switch_configs)
                os.remove(os.path.join(self.configs['model_path'], "model_dore"))
            else:
                logging.warning("loaded a model WITHOUT encryption")
                self.configs['model_filename'] = "model_decore"
                is_loaded_param = self._loadModel(switch_configs)
            assert self.model_object is not None
            if not is_loaded_param:
                self._loadParameter(switch_configs)
            # preheat
            if self.configs.get('preheat') is not None:
                load_status.value = Status.Preheating.value
                self.enqueueData({'uuid': "preheat", 'path': self.configs['preheat']})
                self._inferData(self.configs['model_name']+self.configs['version'], 1)
            # predicting loop
            load_status.value = Status.Running.value
            while True:
                if self.state.value == State.Exiting.value:
                     break
                id_lists, result_lists = self._inferData(
                    self.configs['model_name']+self.configs['version'],
                    self.configs['batchsize'])
                for i in range(self.configs['batchsize']):
                    self.configs['queue.in'].set(id_lists[i], self.dumpData(result_lists[i]))
            load_status.value = Status.Exited.value
        except Exception as e:
            if runtime.dev_debug:
                logging.exception(e)
            else:
                logging.error(e)
            load_status.value = Status.Cleaning.value
            self.model_object = None
            load_status.value = Status.Error.value

    def enqueueData(self, infer_data):
        self.configs['queue.in'].rpush(
                 self.configs['model_name']+self.configs['version'],
                 self.dumpData(infer_data))

    def reportStatus(self):
        status_vector = {'state': self.state.value}
        if self.state.value >= State.Loading.value:
            for i in range(0, self.configs['inferproc_num']):
                status_vector[str(i)] = self.inferproc_state[i].value
        return {
            'model'  : self.configs['model_name'],
            'status' : self.dumpData(status_vector),
            'msg'    : "backend error: {}",
        }

    def terminate(self):
        _, exit = self.inferproc_all_exit()
        if exit:
            self.state.value = State.Exited.value
            return {'code': 0, 'msg': ""}
        else:
            return {'code': 1, 'msg': "some inference process haven't finished"}

    @abc.abstractmethod
    def _loadModel(self, load_configs):
        logging.critical("AbstractBackend::_loadModel called")
        exit(-1)

    @abc.abstractmethod
    def _loadParameter(self, load_configs):
        logging.critical("AbstractBackend::_loadParameter called")
        exit(-1)

    @abc.abstractmethod
    def _inferData(self, infer_data, batchsize):
        logging.critical("AbstractBackend::_inferData called")
        exit(-1)

    @utils.profiler_timer("AbstractBackend::dumpData")
    def dumpData(self, data):
        return json.dumps(data)

    @utils.profiler_timer("AbstractBackend::loadData")
    def loadData(self, data):
        return json.loads(data)


