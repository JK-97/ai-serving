import os
import uuid
import json
import shutil
import tarfile
import logging
from serving import utils
from serving.backend import abstract_backend as ab
from serving.backend import supported_backend as sb
from settings import settings


def listStoredModel():
    models = {}
    storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    for m in os.listdir(os.path.join(storage, "models")):
        ver_list = os.listdir(os.path.join(storage, "models", m))
        models[m] = ver_list
    return models


def checkModelExist(name, version):
    storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    path = os.path.join(storage, "models", name, version)
    return path, os.path.exists(path)


def encryptModel():
    pass


def decryptModel():
    pass


def packBundle(model_name, model_version):
    try:
        model_path, exist = checkModelExist(model_name, model_version)
        if not exist:
           return {'code': 1, 'msg': "failed to find requested model: "+model_name+"("+model_version+")"}
        else:
            target_name = str(uuid.uuid4())
            tmpdir = os.path.join("/tmp", target_name)
            shutil.copytree(model_path, os.path.join("/tmp", tmpdir))

            # distros.json -> configs.json
            distro = {}
            with open(os.path.join(tmpdir, "distros.json"), "r") as distro_file:
                distro = json.loads(distro_file.read())
            config = {
                'labels':  distro['labels'],
                'backend': distro['backend'],
            }
            os.remove(os.path.join(tmpdir, "distros.json"))
            with open(os.path.join(tmpdir, "configs.json"), 'w') as config_file:
                 config_file.write(json.dumps(distro, indent=2))

            if os.path.exists(os.path.join(tmpdir, "__pycache__")):
                shutil.rmtree(os.path.join(tmpdir, "__pycache__"))

            # compress
            tar = tarfile.open(os.path.join("/tmp", target_name+".tar.gz"), "w:gz")
            tar.add(tmpdir, arcname=model_name+"/"+model_version)
            tar.close()
            # clean tmp files
            shutil.rmtree(tmpdir)
            return target_name
    except Exception as e:
        logging.exception(e)
        return None


def unpackBundle(bundle_id, dist_info):
    try:
        bundle_path = os.path.join("/tmp", bundle_id+".tar.gz")
        if not os.path.exists(bundle_path):
            return {'code': 1, 'msg': "failed to find requested package: "+bundle_id}
        else:
            tar = tarfile.open(bundle_path, "r")
            tar.extractall("/tmp")
            tar.close()

            # configs.json -> distros.json
            distro = {}
            content_path = os.path.join("/tmp", dist_info['model'], dist_info['version'])
            with open(os.path.join(content_path, "configs.json"), 'r') as config_file:
                distro = json.loads(config_file.read())
            distro['md5'] = dist_info['md5']
            distro['model'] = dist_info['model']
            distro['version'] = dist_info['version']
            distro['mapping'] = dist_info['mapping']
            distro['threshold'] = dist_info['threshold']
            os.remove(os.path.join(content_path, "configs.json"))
            with open(os.path.join(content_path, "distros.json"), 'w') as distro_file:
                distro_file.write(json.dumps(distro, indent=2))

            storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
            target_model_path = os.path.join(storage, "models", dist_info['model'])
            if not os.path.exists(target_model_path):
                os.makedirs(target_model_path)
            if os.path.exists(os.path.join(target_model_path, dist_info['version'])):
                return {'code': 1, 'msg': "version exist"}
            else:
                shutil.move(os.path.join("/tmp", dist_info['model'], dist_info['version']),
                            os.path.join(target_model_path, dist_info['version']))
                shutil.rmtree(os.path.join("/tmp", dist_info['model']))
                os.remove(bundle_path)
            return {'code': 0, 'msg': bundle_id}
    except Exception as e:
        logging.exception(e)
        return {'code': 1, 'msg': "unpack failed"}
