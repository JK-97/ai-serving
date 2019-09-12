import tornado.web
import tornado.gen


class BaseHandler(tornado.web.RequestHandler):
    def arthur(self):
        pass


class AsyncHandler(BaseHandler):
    @property
    def executor(self):
        return self.application.executor

    @tornado.gen.coroutine
    def async_worker(self, func, data):
        status, result = yield self.executor.submit(func, (data))
        if status == 200:
            return 200, result
        else:
            return status, result

    def do_post(self, data):
        return 404, "async handler"

    def do_get(self, data):
        return 404, "async handler"

    def post(self):
        data = json.loads(data)
        return self.async_worker(self.do_post, data)

    def get(self):
        data = json.loads(data)
        return self.async_worker(self.do_get, data)
