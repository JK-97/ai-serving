"""
  JXServing Tensorflow Serving Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import socket
import logging
import requests
from contextlib import closing
from serving import utils
from serving.backend import abstract_backend as ab


class TfSrvBackend(ab.AbstractBackend):
    def __init__(self, collection, configurations = {}):
        super().__init__(collection, configurations)
        host = utils.getKey('host', dicts=self.configurations)
        port = utils.getKey('port', dicts=self.configurations)
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((host, int(port))) != 0:
                logging.critical("Failed to connect {}:{}".format(host, port))
        self.base_url = "http://"+host+":"+port+"/v1/models/{}:predict"

    @utils.profiler_timer("TfSrvBackend::_loadModel")
    def _loadModel(self, load_configs):
        ver_dirs = os.listdir(self.current_model_path)
        latest_ver = -1
        for d in ver_dirs:
            if os.path.isdir(os.path.join(self.current_model_path, d)):
                try:
                    if int(d) > latest_ver:
                        latest_ver = int(d)
                except ValueError as e:
                    continue
        if latest_ver > 0:
            logging.info("Using version <{}> of model {}".format(latest_ver, self.current_model_name))
            tmp_path = os.path.join(self.current_model_path, str(latest_ver))
        else:
            raise RuntimeError("Cannot find a loadable version of {}".format(self.current_model_name))
        self.current_model_path = tmp_path

        with open(os.path.join(self.current_model_path, 'class.txt')) as class_file:
            self.classes = eval(class_file.read().encode('utf-8'))
        self.model_object = "tensorflow-serving"
        return True

    @utils.profiler_timer("TfSrvBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfSrvBackend::_inferData")
    def _inferData(self, pre_p):
        feeding = self._dumpsData({
            'inputs'         : utils.getKey('feed_list', dicts=pre_p),
            'signature_name' : "predict",
        })
        request_url = self.base_url.format(self.current_model_name)
        ret = requests.post(request_url, data = feeding)
        return self._loadsData(ret.text)

