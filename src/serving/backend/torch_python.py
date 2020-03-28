"""
  AIServing PyTorch Backend

  Contact: 1179160244@qq.com
"""

import os
import sys
import torch
import json
import logging
import importlib
import collections
from enum import Enum, unique
from serving import utils
from serving.backend import abstract_backend as ab
from settings import settings


@unique
class ModelType(Enum):
    StructureEmbed = 'structureEmbed'
    StructureSplit = 'structureSplit'


def ModelTypeValidator(value):
    try:
        return ModelType(value), ""
    except ValueError as e:
        return None, "unsupported model type"


class TorchPyBackend(ab.AbstractBackend):
    @utils.profiler_timer("TorchPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        model_type = utils.getKey(
            'm',
            {'m': str.split(self.model_configs['impl'], ".")[1]},
            v=ModelTypeValidator)
        if model_type == ModelType.StructureEmbed:
            return self._loadStructEmbedModel(load_configs)
        if model_type == ModelType.StructureSplit:
            return self._loadStructSplitModel(load_configs)
        return True

    def _loadStructEmbedModel(self, load_configs):
        logging.error('Currently not impl structure embedded model')
        return True

    def _loadStructSplitModel(self, load_configs):
        sys.path.append(self.model_path)
        model_loader = importlib.import_module('model')
        self.model_object = model_loader.build_structure()
        self.model_object.to(self._getDevice(load_configs))
        return False

    @utils.profiler_timer("TorchPyBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        path = os.path.join(self.model_path, "param.pth")
        device = utils.getKey(
            'be.trpy.device', dicts=settings, level=utils.Access.Optional)
        if device == None:
            device = 'cpu'
        logging.debug("torch load parameters on: {})".format(device))
        parameters = torch.load(path, map_location=device)['state_dict']

        mixed_mode = utils.getKey('be.trpy.mixed_mode', settings)
        if mixed_mode == '1':
            current_state = self.model_object.state_dict()
            new_state = collections.OrderedDict()
            for key, _ in current_state.items():
                if key in parameters and parameters[key].size() == current_state[key].size():
                    new_state[key] = parameters[key]
                else:
                    new_state[key] = current_state[key]
                    logging.warning(
                        'not found pre-trained parameters for {}'.format(key))
            self.model_object.load_state_dict(new_state)
        else:
            self.model_object.load_state_dict(parameters)
        self.model_object.eval()

    @utils.profiler_timer("TorchPyBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize != 1:
            raise Exception("batchsize unequal one")
        id_lists, feed_lists, passby_lists = self.__buildBatch(
            input_queue, batchsize)
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(
            passby_lists, infer_lists, batchsize)
        return id_lists, result_lists

    @utils.profiler_timer("TorchPyBackend:::__buildBatch")
    def __buildBatch(self, in_queue, batchsize):
        predp_data = [None] * batchsize
        id_lists = [None] * batchsize
        feed_lists = [None] * batchsize
        passby_lists = [None] * batchsize
        index = batchsize - 1
        package = self.configs['queue.in'].blpop(in_queue)
        if package is not None:
            predp_frame = json.loads(package[-1].decode("utf-8"))
            id_lists[index] = predp_frame['uuid']
            predp_data[index] = self.predp.pre_dataprocess(predp_frame)
            feed_lists[index] = predp_data[index]['feed_list']
            passby_lists[index] = predp_data[index]['passby']
        return id_lists, feed_lists[index], passby_lists[index]

    @utils.profiler_timer("TorchPyBackend::__inferBatch")
    def __inferBatch(self, feed_lists):
        return self.model_object(feed_lists)

    @utils.profiler_timer("TorchPyBackend::__processBatch")
    def __processBatch(self, passby_lists, infer_lists, batchsize):
        result_lists = [None] * batchsize
        index = batchsize - 1
        post_frame = {
            'passby': passby_lists,
            'infers': infer_lists,
        }
        result_lists[index] = self.postdp.post_dataprocess(post_frame)
        return result_lists

    def _getDevice(self, load_configs):
        device = utils.getKey(
            'be.trpy.device', dicts=settings, level=utils.Access.Optional)
        logging.debug(device)
        if device == None:
            device = 'cpu'
        logging.debug("torch get device on: {}".format(device))
        if 'cuda' in device:
            torch.backends.cudnn.benchmark = True
            logging.debug("set torch.backends.cudnn.benchmark = True")
        return torch.device(device)
