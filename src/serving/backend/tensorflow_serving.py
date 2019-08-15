"""
  JXServing Tensorflow Serving Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
import time
import socket
import logging
import requests
import importlib
from contextlib import closing
from tornado.options import options
from serving import utils
from serving.backend import abstract_backend as ab
from settings import settings


class TfSrvBackend(ab.AbstractBackend):
    def __init__(self, collection, settings = {}):
        super().__init__(collection, settings)
        host = utils.getKeyFromDicts('host', dicts=settings)
        port = utils.getKeyFromDicts('port', dicts=settings)
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((host, int(port))) != 0:
                logging.critical("Failed to connect {}:{}".format(host, port))
                exit(-1)

        self.base_url = "http://"+host+":"+port+"/v1/models/{}:predict"
        logging.debug("TfSrvBackend initialized")

    @utils.profiler_timer("TfSrvBackend::switchModel")
    def switchModel(self, switch_data):
        try:
            model = utils.getKeyFromDicts('model', dicts=switch_data)

            if self.current_model_name == model:
                return True

            self.current_model_name    = model
            self.switch_status         = ab.Status.Loading
            self.switch_error_message  = ""

            tmp_path = os.path.join(self.collection_path, model)
            if not os.path.isdir(tmp_path):
                raise RuntimeError("model does not exist: {}".format(tmp_path))
            ver_dirs = os.listdir(tmp_path)
            latest_ver = -1
            for d in ver_dirs:
                if os.path.isdir(os.path.join(tmp_path, d)):
                    try:
                        if int(d) > latest_ver:
                            latest_ver = int(d)
                    except ValueError as e:
                        continue
            if latest_ver > 0:
                logging.info("Using version <{}> of model {}".format(latest_ver, model))
                tmp_path = os.path.join(tmp_path, str(latest_ver))
            else:
                logging.critical("Cannot find a loadable version of {}".format( model))

            self.current_model_path    = tmp_path

            with open(os.path.join(self.current_model_path, 'class.txt')) as class_file:
                self.classes = eval(class_file.read().encode('utf-8'))
            self.switch_status         = ab.Status.Loaded
            return True
        except Exception as e:
            logging.error(e)
            logging.exception(e)
            self.switch_status = ab.Status.Failed
            self.switch_error_message = "switch error: {}".format(e)
            return False

    @utils.profiler_timer("TfSrvBackend::runSingleSession")
    def runSingleSession(self, filepath):
        try:
            original_image, feed_list = self.preDataProcessing(filepath)
            feeding = self._dumpsData({
                'inputs'         : feed_list,
                'signature_name' : "predict",
            })
            request_url = self.base_url.format(self.current_model_name)
            ret = requests.post(request_url, data = feeding)
            predict = self._loadsData(ret.text)
            return self.postDataProcessing(original_image, predict, self.classes)
        except Exception as e:
            logging.exception(e)
            logging.error("failed to run session: {}".format(e))
            return None

"""
    @utils.profiler_timer("TfSrvBackend::preDataProcessing")
    def preDataProcessing(self, path):
        if self.predp:
            return self.predp.pre_dataprocess(path)
        else:
            try:
                sys.path.append(self.current_model_path)
                self.predp = importlib.import_module('pre_dataprocess')
                return self.predp.pre_dataprocess(path)
            except Exception as e:
                logging.critical(e)
                logging.exception(e)
                raise e

    @utils.profiler_timer("TfSrvBackend::postDataProcessing")
    def postDataProcessing(self, original_image, prediction_dict, classes):
        if self.postdp:
            return self.postdp.post_dataprocess(original_image, prediction_dict, classes)
        else:
            try:
                sys.path.append(self.current_model_path)
                self.postdp = importlib.import_module('post_dataprocess')
                return self.postdp.post_dataprocess(original_image, prediction_dict, classes)
            except Exception as e:
                logging.critical(e)
                logging.exception(e)
                raise e
"""
