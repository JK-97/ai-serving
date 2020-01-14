class RunTimeException(Exception):
    code = 1
    msg = 'runtime error'

    def __init__(self, code=None, msg=None):
        if code:
            self.code = code
        if msg:
            self.msg = msg
        super(RunTimeException, self).__init__(msg)


class ConstrainBackendInfoError(RunTimeException):
    code = 100


class LimitBackendError(RunTimeException):
    code = 101
    msg = 'backend instance exceed limitation'


class ExistBackendError(RunTimeException):
    code = 102
    msg = 'backend has running'


class FullHashValueError(RunTimeException):
    code = 103
    msg = 'fullhash value error'


class ImportModelDistroError(RunTimeException):
    code = 104
    msg = "import model error"


class DeleteModelError(RunTimeException):
    code = 105
    msg = "delete model error"


class CreateAndLoadModelError(RunTimeException):
    code = 106
    msg = "create and load model error"


class ReloadModelOnBackendError(RunTimeException):
    code = 107
    msg = "create and load model error"


class TerminateBackendError(RunTimeException):
    code = 108
    msg = "terminate backend error"


class ListOneBackendError(RunTimeException):
    code = 109
    msg = "query list backend error"


class InferenceDataError(RunTimeException):
    code_local = 110
    code_remote = 111
    msg = 'inference data error'


class UpdateModelError(RunTimeException):
    code = 112
    msg = "update model error"
