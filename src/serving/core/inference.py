import os

from serving import utils
from serving.core import runtime
from serving.core.error_code import InferenceDataError



@utils.gate(runtime.FGs['use_native_stat'], runtime.Ps['native_stat'])
def inferenceLocal(data):
    backend_instance = runtime.BEs.get(data.get('bid'))
    if backend_instance is None:
        raise RuntimeError("failed to find backend")
    data_id = data.get('uuid')
    if data_id is None:
        raise ValueError("lack of data_id")
    if data.get('path'):
        index = "local"
        runtime.Images_pool[index] = utils.imread_image(data.get('path'))
    elif data.get('type'):
        index = data.get('type')
    else:
        raise ValueError("lack of data_path")
    backend_instance.enqueueData({'uuid': data_id, 'image_type': index})



@utils.gate(runtime.FGs['use_native_stat'], runtime.Ps['native_stat'])
def inferenceRemote(data):
    backend_instance = runtime.BEs.get(data.get('bid'))
    if backend_instance is None:
        raise InferenceDataError(msg="failed to find backend")
    data_id = data.get('uuid')
    data_src = data.get('base64')
    data_type = data.get('type')

    if data_id is None or data_src is None or data_type is None:
        raise InferenceDataError(msg="lack of data")

    # TODO(): directly transfer base64 data to memory
    tmp_file = os.path.join('/tmp', data_id + '.' + data_type)
    ret = runtime.Ps['encbase64'].to_image(data_src, tmp_file)
    if ret['code'] != 0:
        raise RuntimeError("failed to dump remote data")
    index = "remote"
    runtime.Images_pool[index] = utils.imread_image(tmp_file)
    backend_instance.enqueueData({'uuid': data_id, 'image_type': index})
