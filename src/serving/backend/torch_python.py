"""
  JXServing PyTorch Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
import cupy
import torch
import logging
import importlib
import collections
from enum import Enum, unique
from serving import utils
from serving.backend import abstract_backend as ab


@unique
class ModelType(Enum):
    StructureEmbed  = 'structureEmbed'
    StructureSplit  = 'structureSplit'


def ModelTypeValidator(value):
    try:
        return ModelType(value), ""
    except ValueError as e:
        return None, "unsupported model type"


class TorchPyBackend(ab.AbstractBackend):
    @utils.profiler_timer("TorchPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        model_type = utils.getKey('mode', dicts=load_configs, v=ModelTypeValidator)
        if model_type == ModelType.StructureEmbed:
            return self._loadStructEmbedModel(load_configs)
        if model_type == ModelType.StructureSplit:
            return self._loadStructSplitModel(load_configs)
        return True

    def _loadStructEmbedModel(self, load_configs):
        logging.error('Currently not impl structure embedded model')
        return True

    def _loadStructSplitModel(self, load_configs):
        sys.path.append(self.current_model_path)
        model_loader = importlib.import_module('model')
        self.model_object = model_loader.build_structure()
        self.model_object.to(self._getDevice(load_configs))
        return False

    @utils.profiler_timer("TorchPyBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        path = os.path.join(self.current_model_path, "param.pth")
        device = utils.getKey('device', dicts=load_configs, level=utils.Access.Optional)
        if device == None:
            device = 'cpu'
        logging.debug("torch load parameters on: {})".format(device))
        parameters = torch.load(path, map_location=device)['state_dict']

        mixed_mode = utils.getKey('mixed_mode', dicts=self.configurations)
        if mixed_mode == '1':
            current_state = self.model_object.state_dict()
            new_state = collections.OrderedDict()
            for key, _ in current_state.items():
                if key in parameters and parameters[key].size() == current_state[key].size():
                    new_state[key] = parameters[key]
                else:
                    new_state[key] = current_state[key]
                    logging.warning('not found pre-trained parameters for {}'.format(key))
            self.model_object.load_state_dict(new_state)
        else:
            self.model_object.load_state_dict(parameters)
        self.model_object.eval()

    @utils.profiler_timer("TorchPyBackend::_inference")
    def _inferData(self, infer_data):
        return (self.model_object(infer_data['input']))

    def _getDevice(self, load_configs):
        device = utils.getKey('device', dicts=load_configs, level=utils.Access.Optional)
        if device == None:
            device = 'cpu'
        logging.debug("torch get device on: {}".format(device))
        if 'cuda' in device:
            torch.backends.cudnn.benchmark = True
            logging.debug("set torch.backends.cudnn.benchmark = True")
        return torch.device(device)

