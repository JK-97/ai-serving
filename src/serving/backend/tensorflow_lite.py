import os
import logging
import numpy as np
import tensorflow as tf
from serving import utils
from serving.backend import abstract_backend as ab

class TfLiteBackend(ab.AbstractBackend):
    def __init__(self, collection, configurations = {}):
        super().__init__(collection, configurations)

    @utils.profiler_timer("TfLiteBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
            # load model pb
            self.model_object = tf.lite.Interpreter(model_path=os.path.join(self.current_model_path, "model.tflite"))
            self.model_object.allocate_tensors()
            self.input_details = self.model_object.get_input_details()
            self.output_details = self.model_object.get_output_details()
            return True
        except Exception as e:
            raise e

    @utils.profiler_timer("TfLiteBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfLiteBackend::_inferData")
    def _inferData(self, pre_p):
        self.model_object.set_tensor(self.input_details[0]['index'], pre_p[0])
        self.model_object.invoke()
        self.output_res = []
        for i in range(0, len(self.output_details)):
            self.output_res.append(self.model_object.get_tensor(self.output_details[i]['index']).squeeze())
        self.output_res.append(pre_p)
        return self.output_res




