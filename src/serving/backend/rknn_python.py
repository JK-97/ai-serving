"""
  JXServing RKNN Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
from rknn.api import RKNN
from serving import utils
from serving.backend import abstract_backend as ab


class RKNNPyBackend(ab.AbstractBackend):
    def __del__(self):
        if self.model_object is not None:
            self.model_object.release()

    @utils.profiler_timer("RKNNPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        rk_target = utils.getKey('target', dicts=self.configurations)

        self.model_object = RKNN()
        path = os.path.join(self.current_model_path, "models.rknn")
        self.model_object.load_rknn(path)
        ret = self.model_object.init_runtime(target = rk_target)
        if ret != 0:
            raise RuntimeError("Failed to initialize RKNN runtime enrvironment")
        return True

    @utils.profiler_timer("RKNNPyBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("RKNNPyBackend::_inferData")
    def _inferData(self, pre_p):
        return self.model_object.inference(
                inputs  = utils.getKey('inputs', dicts=pre_p),
                data_type = utils.getKey('data_type', dicts=pre_p))

