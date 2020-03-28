"""
  AIServing Tensorflow Serving Backend

  Contact: 1179160244@qq.com
"""

import os
import socket
import logging
import requests
import json
from contextlib import closing
from serving import utils
from serving.backend import abstract_backend as ab
from settings import settings


class TfSrvBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)
        host = utils.getKey('be.tfsrv.host', dicts=settings)
        port = utils.getKey('be.tfsrv.rest_port', dicts=settings)
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((host, int(port))) != 0:
                logging.critical("Failed to connect {}:{}".format(host, port))
        self.base_url = "http://"+host+":"+port+"/v1/models/{}:predict"

    @utils.profiler_timer("TfSrvBackend::_loadModel")
    def _loadModel(self, load_configs):
        path = os.path.join(
            self.backend_configs['storage'], "models", self.model_configs['implhash'])
        ver_dirs = os.listdir(path)
        latest_ver = -1
        for d in ver_dirs:
            if os.path.isdir(os.path.join(path, d)):
                try:
                    if int(d) > latest_ver:
                        latest_ver = int(d)
                except ValueError as e:
                    continue
        if latest_ver > 0:
            logging.info("Using version <{}> of model {}".format(
                latest_ver, self.model_configs["name"]))
        else:
            raise RuntimeError("Cannot find a loadable version of {}".format(
                self.model_configs["name"]))
        self.model_object = "tensorflow-serving"
        return True

    @utils.profiler_timer("TfSrvBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfSrvBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize != 1:
            raise Exception("batchsize unequal one")
        id_lists, feed_lists, passby_lists = self.__buildBatch(
            input_queue, batchsize)
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(
            passby_lists, infer_lists, batchsize)
        return id_lists, result_lists

    @utils.profiler_timer("TfSrvBackend::__buildBatch")
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

    @utils.profiler_timer("TfSrvBackend::__inferBatch")
    def __inferBatch(self, feed_lists):
        logging.debug(self.model_configs)
        feeding = json.dumps({
            'inputs': feed_lists,
            'signature_name': "predict",
        })
        request_url = self.base_url.format(self.model_configs["name"])
        logging.debug("url::{}".format(request_url))
        ret = requests.post(request_url, data=feeding)
        return json.loads(ret.text)

    @utils.profiler_timer("TfSrvBackend::__processBatch")
    def __processBatch(self, passby_lists, infer_lists, batchsize):
        labels = self.model_configs.get('labels')
        result_lists = [None] * batchsize
        index = batchsize - 1
        post_frame = {
            'passby': passby_lists,
            'infers': infer_lists,
            'labels': labels,
        }
        result_lists[index] = self.postdp.post_dataprocess(post_frame)
        return result_lists
