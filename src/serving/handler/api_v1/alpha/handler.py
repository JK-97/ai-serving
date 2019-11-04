import logging

import rapidjson as json

from serving.core import runtime
from serving.handler.base import BaseHandler, AsyncHandler


class DetectHandler(AsyncHandler):
    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        try:
            data = str(self.request.body, encoding="utf-8")
            self.finish(runtime.inputData(json.loads(data)))
        except KeyError as e:
            logging.exception(e)
            self.finish({"err": 400, "msg": "missing key {}".format(e)})
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")


class SwitchModelHandler(BaseHandler):
    def get(self, *args, **kwargs):
        try:
            self.finish(runtime.reporter())
        except KeyError as e:
            logging.exception(e)
            self.finish({"err": 400, "msg": "missing key {}".format(e)})
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")

    def post(self, *args, **kwargs):
        try:
            data = str(self.request.body, encoding="utf-8")
            ret = runtime.createAndLoadBackends(json.loads(data))
            self.finish(ret)
        except KeyError as e:
            logging.exception(e)
            self.send_error_response(status_code=400, message="missing key {}".format(e))
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")
