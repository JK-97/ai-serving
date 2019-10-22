"""
  JXServing Tensorflow Python Backend
"""
import os
import sys

import mxnet as mx
import numpy as np
import rapidjson as json
from sklearn import preprocessing
from enum import Enum

from serving import utils
from serving.backend import abstract_backend as ab


class ModelType(Enum):
    MODEL_1 = 0
    MODEL_2 = 1
    MODEL_3 = 2
    MODEL_4 = 3


class MxNetBackend(ab.AbstractBackend):
    def __init__(self, collection, settings={}):
        super().__init__(collection, settings)
        self.pre_model = None
        self.image_size = utils.getKey("face_image_size", dicts=settings)
        self.identify_path = utils.getKey("mxnet_identifier_suffix", dicts=settings)
        self.json_path = utils.getKey("mxnet_json_path", dicts=settings)
        arch = utils.getKey('arch', dicts=settings)
        if arch == 1:
            self.ctx = mx.cpu()
        else:
            self.ctx = mx.gpu(arch)

    @utils.profiler_timer("MxNetBackend::_loadModel")
    def _loadModel(self, load_data):
        sys.path.append(self.current_model_path)
        detection_path = os.path.join(self.current_model_path, "detection")
        sys.path.append(detection_path)
        self.model_type = ModelType(load_data['type'])
        self.identify_path = os.path.join(self.current_model_path, self.identify_path)
        # # load 4 models from folder
        models = ['det1', 'det2', 'det3']
        models = [os.path.join(detection_path, f) for f in models]
        self.model_object = self.load_model(models, self.model_type.value)
        # load json refer names & refer values
        if self.model_type == ModelType.MODEL_4:
            self.refer_vals = []
            self.refer_names = []
            json_path = self.current_model_path + self.json_path
            with open(json_path, 'r') as jsf:
                name_val_path = json.load(jsf)
                for name, val in name_val_path.items():
                    self.refer_names.append(name)
                    self.refer_vals.append(val[0])
            self.refer_vals = np.array(self.refer_vals)
        self.current_model_path = self.collection_path

    def _loadParameter(self, load_data):
        return True

    def _inferData(self, infer_data):
        promise = {
            ModelType.MODEL_1: self.detect_model1,
            ModelType.MODEL_2: self.detect_model2,
            ModelType.MODEL_3: self.detect_model3,
            ModelType.MODEL_4: self.identify_model,
        }
        data_list = promise[self.model_type](infer_data)
        return data_list

    def load_model(self, models, num):
        if num == ModelType.MODEL_4.value:
            model = self.get_identify_model(self.ctx, self.image_size, self.identify_path, 'fc1')
        else:
            if num >= len(models):
                raise ValueError('type value error')
            model = mx.model.FeedForward.load(models[num], 1, ctx=self.ctx)
        return model

    @staticmethod
    def get_identify_model(ctx, image_size, model_path, layer):
        _vec = model_path.split(',')
        assert len(_vec) == 2
        prefix = _vec[0]
        epoch = int(_vec[1])
        sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
        all_layers = sym.get_internals()
        sym = all_layers[layer + '_output']
        model = mx.mod.Module(symbol=sym, context=ctx, label_names=None)
        model.bind(data_shapes=[('data', (1, 3, image_size[0], image_size[1]))])
        model.set_params(arg_params, aux_params)
        return model

    @utils.profiler_timer("MxNetBackend::detect_model1")
    def detect_model1(self, infer_data):
        infer_data = infer_data['pre']
        output_list = []
        input_buff_list, scales, threshold, img = infer_data
        if len(input_buff_list) != len(scales):
            raise Exception("array list not match")
        for input_buff in input_buff_list:
            output_list.append(self.model_object.predict(input_buff))
        return output_list, scales, threshold, img

    @utils.profiler_timer("MxNetBackend::detect_model2")
    def detect_model2(self, infer_data):
        infer_data = infer_data['pre']
        boxes, input_buff_list, img = infer_data
        output = self.model_object.predict(input_buff_list)
        return boxes, output, img

    @utils.profiler_timer("MxNetBackend::detect_model3")
    def detect_model3(self, infer_data):
        infer_data = infer_data['pre']
        boxes, input_buff_list, img = infer_data
        output = self.model_object.predict(input_buff_list)
        return boxes, output, img

    @utils.profiler_timer("MxNetBackend::identify_model")
    def identify_model(self, infer_data):
        infer_data = infer_data['pre']
        output_list = []
        data_iter, imgs, init_bboxes = infer_data
        for batch_faces in data_iter:
            self.model_object.forward(batch_faces, is_train=False)
            embedding = self.model_object.get_outputs()
            for em in embedding[0]:
                em = preprocessing.normalize([em.asnumpy()]).flatten()
                output_list.append(em)
        return output_list, imgs, init_bboxes, (self.refer_vals, self.refer_names)
