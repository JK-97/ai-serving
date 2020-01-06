def error_msg(c_pb2, error, exception=None, msg=None):
    if exception is not None:
        return c_pb2.ResultReply(
            code=error.code,
            msg=repr(exception))
    else:
        return c_pb2.ResultReply(
            code=error.code,
            msg=msg)
