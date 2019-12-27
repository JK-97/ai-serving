import os
import uuid
import json
import shutil
import hashlib
import tarfile
import logging
from serving import utils
from settings import settings


def createModel(model):
    model['implhash'] = generateModelImplHashByExtractInfo(model)

    if checkModelExist(model['implhash'], model['version']):
        raise RuntimeError("model already exists")
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    os.makedirs(os.path.join(storage_path, "models", model['implhash'], model['version']))
    dumpModelInfoToStorage(model['implhash'], model['version'], model)


def listModels(simple=False):
    model_list = []
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    for m in os.listdir(os.path.join(storage_path, "models")):
        for v in os.listdir(os.path.join(storage_path, "models", m)):
            detail = loadModelInfoFromStorage(m, v)
            model_list.append(detail)
    return {'models': model_list}


def updateModel(model):
    if not checkModelExist(model['implhash'], model['version']):
        raise RuntimeError("requested model not exist")
    old_dist = loadModelInfoFromStorage(model['implhash'], model['version'])
    if old_dist['implhash'] != model['implhash']:
        raise RuntimeError("incompatible model")
    model['disthash'] = generateModelDistHashByExtractInfo(model)
    dumpModelInfoToStorage(model['implhash'], model['version'], model)


def deleteModel(model):
    if model.get('implhash') is None:
        model['implhash'] = generateModelImplHashByExtractInfo(model)
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    model_path = os.path.join(storage_path, "models", model['implhash'], model['version'])
    if not os.path.exists(model_path):
        raise RuntimeError("model not exist")
    shutil.rmtree(model_path)


def buildImageBundleFromDistroBundle(model):
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    if not model.get('implhash'):
        model['implhash'] = generateModelImplHashByExtractInfo(model)
    model_hash = model['implhash']
    model_version = model['version']
    # model_path = os.path.join(storage_path, "models", model_hash, model_version)

    tmp_path = os.path.join("/tmp", model_hash)
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    shutil.copytree(os.path.join(storage_path, "models", model_hash, model_version), tmp_path)

    # distros.json -> configs.json
    distro = loadModelInfoFromStorage(model_hash, model_version)
    del(distro['threshold'])
    del(distro['mapping'])
    del(distro['disthash'])
    os.remove(os.path.join(tmp_path, "distros.json"))

    with open(os.path.join(tmp_path, "configs.json"), 'w') as config_file:
            config_file.write(json.dumps(distro, indent=2))

    if os.path.exists(os.path.join(tmp_path, "__pycache__")):
        shutil.rmtree(os.path.join(tmp_path, "__pycache__"))

    # compress
    tar = tarfile.open(os.path.join("/tmp", model_hash+".tar.gz"), "w:gz")
    tar.add(tmp_path, arcname=model_hash)
    tar.close()
    # clean tmp files
    shutil.rmtree(tmp_path)


def unpackImageBundleAndImportWithDistro(detail):
    bundle_id = detail["bundle"]
    del(detail['bundle'])
    given_implhash = detail['implhash']
    given_version = detail['version']
    bundle_path = os.path.join("/tmp", bundle_id+".tar.gz")
    if not os.path.exists(bundle_path):
        raise RuntimeError("failed to find temporary bundle")
    validateModelInfo(detail)

    # decompress image
    tar = tarfile.open(bundle_path, "r")
    tar.extractall("/tmp")
    tar.close()

    # configs.json -> distros.json, make ImageBundle to DistroBundle
    target_config = {}
    content_path = os.path.join("/tmp", detail['implhash'])
    with open(os.path.join(content_path, "configs.json"), 'r') as config_file:
        target_config = json.loads(config_file.read())

    target_implhash = target_config['implhash']
    target_version = target_config['version']
    if target_implhash != given_implhash:
        raise RuntimeError("incompatible model image")
    os.remove(os.path.join(content_path, "configs.json"))

    # import bundle
    storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    target_model_path = os.path.join(storage, "models", given_implhash)

    if not os.path.exists(target_model_path):
        os.makedirs(target_model_path)
    if os.path.exists(os.path.join(target_model_path, given_version)):
        raise RuntimeError("model already exist with specific version")
    shutil.move(content_path, os.path.join(target_model_path, given_version))
    dumpModelInfoToStorage(given_implhash, given_version, detail)


#
def checkModelExist(model_hash, version):
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    model_path = os.path.join(storage_path, "models", model_hash, version)
    if not os.path.exists(model_path):
        return False
    return True

def validateModelInfo(model):
    if model['implhash'] != generateModelImplHashByExtractInfo(model):
        raise RuntimeError("incompatible model, invalid implementation hash")
    if len(model['labels']) != len(model['threshold']) or len(model['labels']) != len(model['mapping']):
        raise RuntimeError("labels, threshold, mapping incompatible")

def loadModelInfoFromStorage(model_hash, version):
    if not checkModelExist(model_hash, version):
        raise ValueError("model not exist")

    detail = {}
    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    dist_path = os.path.join(storage_path, "models", model_hash, version, "distros.json")
    with open(dist_path, 'r') as dist_file:
        detail = json.loads(dist_file.read())
    return detail

def dumpModelInfoToStorage(model_hash, version, detail):
    if not checkModelExist(model_hash, version):
        raise ValueError("model not exist")

    storage_path = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
    with open(os.path.join(storage_path, "models", model_hash, version, "distros.json"), 'w') as dist_file:
        dist_file.write(json.dumps(detail, indent=2))

def generateModelImplHashByExtractInfo(model):
    hash_string = "{}{}{}{}".format(
        "".join(model['labels']),
        model['head'],
        model['bone'],
        model['impl'],
    )
    return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

def generateModelDistHashByExtractInfo(model):
    hash_string = "{}{}".format(
        "".join(model['threshold']),
        "".join(model['mapping']),
    )
    return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
