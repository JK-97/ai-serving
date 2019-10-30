"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import sys
import redis
import logging
import importlib
import rapidjson as json
from enum import Enum, unique
from multiprocessing import Value
from serving import utils


@unique
class Status(Enum):
    Unloaded   = 0
    Failed     = 1
    Cleaning   = 2
    Loading    = 3
    Preheating = 4
    Running    = 5


@unique
class State(Enum):
    Exit       = 0


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, configurations = {}):
        self.configs = configurations
        self.configs['model_name'] = ""
        self.configs['model_path'] = ""
        self.configs['labels'] = []
        self.configs['threshold'] = {}
        self.configs['batchsize'] = 100
        self.configs['inferproc_num'] = 1

        self.model_object = None
        self.status = {}
        self.predp = None
        self.postdp = None

        self.input_queue = 'input_queue'
        self.output_queue = 'output_queue'
        self.exit_flag = Value('h', 0)

        redisPool_for_raw_data = redis.ConnectionPool(
            host=self.configs['redis.host'],
            port=self.configs['redis.port'],
            db=5)
        self.rPipe_for_raw_data = redis.Redis(connection_pool=redisPool_for_raw_data)

    def initBackend(self, switch_configs):
        try:
            self.configs['model_name'] = utils.getKey('model', dicts=switch_configs)
            # if switch to same model, quick return
            # cleaning
            # loading

            # validate model path
            self.configs['model_path'] = os.path.join(self.configs['storage'], self.configs['model_name'])
            if not os.path.isdir(self.configs['model_path']):
                raise RuntimeError("model does not exist: {}".format(self.configs['model_path']))
            # load customized model pre-process and post-process functions
            sys.path.append(self.configs['model_path'])
            self.predp = importlib.import_module('pre_dataprocess')
            self.postdp = importlib.import_module('post_dataprocess')
            # load extra configurations
            with open(os.path.join(self.configs['model_path'], 'model_config.json')) as config_file:
                self.configs['model_configs'] = self.loadData(config_file.read())
            # start process
            for i in range(0, self.configs['inferproc_num']):
                self.status[i] = Value('B', Status.Unloaded.value)
                self.predictor(switch_configs, self.input_queue, self.output_queue, self.status[i], self.exit_flag)
        except Exception as e:
            logging.exception(e)

    def enqueueData(self, infer_data):
        self.rPipe_for_raw_data.rpush(self.input_queue , self.dumpData(infer_data))

    @utils.process
    def predictor(self, switch_configs, in_queue, out_queue, load_status, exit_flag):
        try:
            # loading model object
            load_status.value = Status.Loading.value
            is_loaded_param = self._loadModel(switch_configs)
            assert self.model_object is not None
            if not is_loaded_param:
                self._loadParameter(switch_configs)
            # preheat
            if self.configs.get('preheat') is not None:
                load_status.value = Status.Preheating.value
                self.enqueueData({'uuid': "preheat", 'path': self.configs['preheat']})
                self._inferData(in_queue, 1)
            # predicting loop
            load_status.value = Status.Running.value
            while True:
                if exit_flag.value == 10:
                     break
                id_lists, result_lists = self._inferData(in_queue, self.configs['batchsize'])
                for i in range(self.configs['batchsize']):
                    self.rPipe_for_raw_data.set(id_lists[i], self.dumpData(result_lists[i]))
        except Exception as e:
            logging.exception(e)
            load_status.value = Status.Cleaning.value
            self.model_object = None
            load_status.value = Status.Failed.value

    def reportStatus(self):
        status_vector = {}
        for i in range(0, self.configs['inferproc_num']):
            status_vector[i] = self.status[i].value
        return {
            'model'  : self.configs['model_name'],
            'status' : status_vector,
            #'error'  : "switch error: {}".format(self.switch_error),
        }

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


