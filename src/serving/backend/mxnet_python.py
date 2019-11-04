"""
  JXServing Tensorflow Python Backend
"""
import os
from enum import Enum

import mxnet as mx
import numpy as np
import rapidjson as json
from sklearn import preprocessing

from serving import utils
from serving.backend import abstract_backend as ab
from settings import settings


class ModelType(Enum):
    MODEL_1 = 0
    MODEL_2 = 1
    MODEL_3 = 2
    MODEL_4 = 3


class MxNetBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)
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
        detection_path = os.path.join(self.configs['model_path'], "detection")
        self.model_type = ModelType(int(load_data['mtype']))
        self.identify_path = os.path.join(self.configs['model_path'], self.identify_path)
        # load 4 models from folder
        models = ['det1', 'det2', 'det3']
        models = [os.path.join(detection_path, f) for f in models]
        self.model_object = self.load_model(models, self.model_type.value)
        # load json refer names & refer values
        if self.model_type == ModelType.MODEL_4:
            self.refer_vals = []
            self.refer_names = []
            json_path = self.configs['model_path'] + self.json_path
            with open(json_path, 'r') as jsf:
                name_val_path = json.load(jsf)
                for name, val in name_val_path.items():
                    self.refer_names.append(name)
                    self.refer_vals.append(val[0])
            self.refer_vals = np.array(self.refer_vals)

    def _loadParameter(self, load_data):
        return True

    def _inferData(self, in_queue, batchsize):
        promise = {
            ModelType.MODEL_1: self.detect_model1,
            ModelType.MODEL_2: self.detect_model2,
            ModelType.MODEL_3: self.detect_model3,
            ModelType.MODEL_4: self.identify_model,
        }
        id_lists, data = promise[self.model_type](in_queue, batchsize)
        return id_lists, data

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
    def detect_model1(self, in_queue, batchsize):
        data = [None] * batchsize
        id_lists = [None] * batchsize

        for i in range(batchsize):
            package = self.rPipe_for_raw_data.blpop(in_queue)
            if package is not None:
                predp_frame = self.loadData(package[-1])
                id_lists[i] = predp_frame['uuid']
                output_list = []
                input_buff_list, scales, threshold, img = self.predp.pre_dataprocess(predp_frame)
                if len(input_buff_list) != len(scales):
                    raise Exception("array list not match")
                for input_buff in input_buff_list:
                    output_list.append(self.model_object.predict(input_buff))
                total_boxes, img = self.postdp.post_dataprocess((output_list, scales, threshold, img))
                d = {'data': (total_boxes, img)}
                data[i] = d
        return id_lists, data

    @utils.profiler_timer("MxNetBackend::detect_model2")
    def detect_model2(self, in_queue, batchsize):
        data = [None] * batchsize
        id_lists = [None] * batchsize

        for i in range(batchsize):
            package = self.rPipe_for_raw_data.blpop(in_queue)
            if package is not None:
                predp_frame = self.loadData(package[-1])
                id_lists[i] = predp_frame['uuid']
                boxes, input_buff_list, img = self.predp.pre_dataprocess(predp_frame)
                output = self.model_object.predict(input_buff_list)
                total_boxes, img = self.postdp.post_dataprocess((boxes, output, img))
                d = {'data': (total_boxes, img)}
                data[i] = d
        return id_lists, data

    @utils.profiler_timer("MxNetBackend::detect_model3")
    def detect_model3(self, in_queue, batchsize):
        data = [None] * batchsize
        id_lists = [None] * batchsize

        for i in range(batchsize):
            package = self.rPipe_for_raw_data.blpop(in_queue)
            if package is not None:
                predp_frame = self.loadData(package[-1])
                id_lists[i] = predp_frame['uuid']
                boxes, input_buff_list, img = self.predp.pre_dataprocess(predp_frame)
                output = self.model_object.predict(input_buff_list)
                total_boxes, points = self.postdp.post_dataprocess((boxes, output, img))
                d = {'data': (total_boxes, points)}
                data[i] = d
        return id_lists, data

    @utils.profiler_timer("MxNetBackend::identify_model")
    def identify_model(self, in_queue, batchsize):
        data = [None] * batchsize
        id_lists = [None] * batchsize

        for i in range(batchsize):
            package = self.rPipe_for_raw_data.blpop(in_queue)
            if package is not None:
                predp_frame = self.loadData(package[-1])
                id_lists[i] = predp_frame['uuid']
                output_list = []
                data_iter, imgs, init_bboxes = self.predp.pre_dataprocess(predp_frame)
                for batch_faces in data_iter:
                    self.model_object.forward(batch_faces, is_train=False)
                    embedding = self.model_object.get_outputs()
                    for em in embedding[0]:
                        em = preprocessing.normalize([em.asnumpy()]).flatten()
                        output_list.append(em)
                total_boxes, img = self.postdp.post_dataprocess(
                    (output_list, imgs, init_bboxes, (self.refer_vals, self.refer_names)))
                data[i] = {'data': (total_boxes, img)}
        return id_lists, data
