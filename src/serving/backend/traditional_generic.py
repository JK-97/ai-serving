"""
  JXServing traditional generic Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
import logging
import cv2
import json
from enum import Enum, unique
from serving import utils
from serving.core import runtime
from serving.core import sandbox
from serving.backend import abstract_backend as ab
from settings import settings


@unique
class ModelType(Enum):
    AlgorithmSingle   = 'algorithmSingle'
    AlgorithmMultiple = 'algorithmMultiple'


def ModelTypeValidator(value):
    try:
        return ModelType(value), ""
    except ValueError as e:
        return None, "unsupported model type"


class TraditionalGenericBackend(ab.AbstractBackend):
    def __init__(self, configurations = {}):
        super().__init__(configurations)
        self.detector_filename = "detector_dore.py"

    @utils.profiler_timer("TraditionalCVBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
           sys.path.append(self.model_path)
           from detector_dore import detector_dore
           self.model_object = detector_dore()
        except Exception as e:
            raise e

    @utils.profiler_timer("TraditionalCVBackend::_accumulateData")
    def _accumulateData(self, accumulate_data):
        self.model_object.accumulate(accumulate_data)


    @utils.profiler_timer("TraditionalCVBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass


    @utils.profiler_timer("TraditionalCVBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize > 1:
            raise Exception("batchsize in this backend must be one")

        model_type = utils.getKey(
            'm',
            {'m': str.split(self.model_configs['impl'], ".")[1]},
            v=ModelTypeValidator)

        if model_type == ModelType.AlgorithmSingle:
            id_lists, results, previous_data = self.__inferAlgorithmSingle(input_queue, batchsize)
        if model_type == ModelType.AlgorithmMultiple:
            previous_frame = self.model_object.previous()
            id_lists, results, previous_data = self.__inferAlgorithmMultiply(input_queue, batchsize, previous_frame)
        self._accumulateData(previous_data[0])

        return id_lists, results


    @utils.profiler_timer("TraditionalCVBackend::_buildBatch")
    def __buildBatch(self, in_queue, batchsize):
        pass


    @utils.profiler_timer("TraditionalCVBackend::_inferBatch")
    def __inferBatch(self, feed_list):
        pass


    @utils.profiler_timer("TraditionalCVBackend::_processBatch")
    def __processBatch(self, infer_lists, passby_lists, batchsize):
        pass


    @utils.profiler_timer("TraditionalCVBackend::_inferAlgorithmSingle")
    def __inferAlgorithmSingle(self, input_queue, batchsize):
        package = self.configs['queue.in'].blpop(input_queue)
        if package is not None:
            # blopop returns: (b'key', b'{...}')
            predp_frame = json.loads(package[-1].decode("utf-8"))
            id_list = predp_frame['uuid']
            predp_data = self.predp.pre_dataprocess(predp_frame)
            passby_list = predp_data['passby']
            detector_data = self.model_object.detect(predp_data)
            result = self.postdp.post_dataprocess(detector_data, passby_list)
        return [id_list], [result], [None]


    @utils.profiler_timer("TraditionalCVBackend::_inferAlgorithmMultiply")
    def __inferAlgorithmMultiply(self, input_queue, batchsize, previous_frame):
        package = self.configs['queue.in'].blpop(input_queue)
        if package is not None:
           predp_frame = json.loads(package[-1].decode("utf-8"))
           id_list = predp_frame['uuid']
           predp_data = self.predp.pre_dataprocess(predp_frame)
           passby_list = predp_data['passby']

           if previous_frame == None:
               return [id_list], [None], [predp_data]
           detector_data = self.model_object.detect(predp_data)
           result = self.postdp.post_dataprocess(detector_data, passby_list)

        return [id_list], [result], [predp_data]
