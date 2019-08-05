from tornado import web
import traceback
import requests


class V1BaseHandler(web.RequestHandler):

    @property
    def edge_box(self):
        return self.settings['edge_box']

    def set_default_headers(self):
        # 后面的*可以换成ip地址，意为允许访问的地址
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')
        self.set_header('Access-Control-Allow-Methods',
                        'POST, GET, PUT, DELETE')

    def send_info_to_ai(self, url, data):
        return requests.post(url, data)

    def write_error(self, status_code, **kwargs):
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            for line in traceback.format_exception(*kwargs['exc_info']):
                self.write(line)
            self.finish()
        else:
            if 'exc_info' in kwargs:
                self.send_error_response(status_code, message="{}:{},ex:{}".format(
                    status_code, self._reason, repr(kwargs['exc_info'][0])))
            else:
                self.send_error_response(
                    status_code, message="{}:{}".format(status_code, self._reason))

    def send_error_response(self, status_code, message="unkown message"):
        self.finish({"status_code": status_code, "message": message})
