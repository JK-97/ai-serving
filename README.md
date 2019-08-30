# JXServing

[Attention] This repo's git ignored all `*.c` file

[Attention] In some system, protobuf will fallback to pure python implementation, which is *much slower*
* `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp` can help to solve

[Attention] Currently only verified on `python3` environment


#### Introduction

* **JXServing** is designed to provide a unify Deep Learning (DL) detection API
  * In the future, this may extend to a complete DL serving project

* Currently supported DL framework: *Tensorflow*, *Tensorflow Serving* and *PyTorch*
  * Working on *MXNet*


#### Components

* `src` stores all source files
* `build_release.py` and `setup.py` is used to build binary
* `CHANGELOG` is used to keep fixing, changing, adding features log
* `Dockerfile` is used to build containerize image
* `ld.conf` is used to link dynamic library inside container building


#### Installation

* Requirements
  * Depends on the backend you are using
  * Ex1. Tensorflow on Jetson GPU
```
apt-get -y install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev
pip3 install -U numpy grpcio absl-py py-cpuinfo psutil portpicker six mock requests gast h5py astor termcolor protobuf keras-applications keras-preprocessing wrapt google-pasta
pip3 install tensorflow-estimator==1.13.0 tensorboard==1.13.0
pip3 install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v42 tensorflow-gpu==1.13.1+nv19.3
```

* Build for release
  * `python3 build_release.py`
  * after above, all release binaries are stored in `release-pack`

* Deployment
  * Copy the whole `release-pack` folder to the path you want

* Deployment by Docker
  * [ ] TODO


#### Usage

* Config `settings.py`
  * set `backend`: supports `tensorflow`, `tensorflow-serving` and `pytorch`
  * set `collection_path`: a directory indicates where to store all models
  * set `security`: [ ] TODO

* Prepare models
  * Copy model folder to the `collection_path` directory mentioned above
  * See more details in **Serving Models** section

* Run (w/ options)
  * format: `python3 run.py [options]`
  * `--port`, run on a specific port, by default is `8080`
  * `--debug`, enter debug mode, print more messages
  * `--profile`, enter profile mode, print profile messages

* Call HTTP Restful API
  * API version (prefix): `/api/v1alpha`
  * `POST` `/api/v1alpha/detect`: block, use to inference an image
```
{
  path: "/absolute/path/of/image"
}
```
    * `Response`
```
{
  status: "success" or "failed"     # status of inference
  result:                           # inference result, depens on models
  message: "inference message"
}
```
  * `POST` `/api/v1alpha/switch`: non-block, use to load or switch a model
```
{
  model:   "model name"             # model's folder name under collection_path
  mode:    "model type"             # indicate which type of model is going to load
  device:  "device name"            # assign work load to a specific device if available
}
```
    * `Response`
```
{
  status: "success"                 # this API will always returns success
}
```
  * `GET` `/api/v1alpha/switch`: block, used to get loading status
    * `Response`
```
{
  model:  "model name"             # the loading model's name
  status: "status"                 # includes: cleaning, loading, preheating, loaded or failed
  error:  "error message"          # error message, if failed to load model
}
```

* See more example under `src/test`


#### Concept

* **JXServing** has the following concept
* For each inference, all data will pass the following workflow
  * Image -> Pre-DataProcess -> DL Framework -> Post-DataProcess
  * Here, Pre/Post-DataProcess, are implemented by the model provider

* Pre-DataProcess
  * `def pre_dataprocess(infer_data):`
  * `infer_data` comes from HTTP Restful request (`/api/v1alpha/detect`)
  * expect to return dictionary object which includes a data frame needed by DL framework

* Post-DataProcess
  * `def post_dataprocess(pre_p, prediction, classes):`
  * `pre_p` is Pre-DataProcess result, `prediction` is DL inference result
  * `classes` is an array contains all classes supported by this DL model
  * expect to return dictionary object which includes a data frame that you want to return to actual users


#### Serving Models

* **JXServing** will automatically serving a model once this model is constrcuted with a conventional structure

* Tensorflow (Frozen)
  * `saved_model.pb`
  * `class.txt`
  * `tensor.json`
  * `pre_dataprocess.py`
  * `post_dataprocess.py`

* Tensorflow (Unfrozen)
  * `saved_model.pb`
  * `variables`
  * `class.txt`
  * `tensor.json`
  * `pre_dataprocess.py`
  * `post_dataprocess.py`


* Tensorflow Serving
  * `saved_model.pb`
  * `class.txt`
  * `pre_dataprocess.py`
  * `post_dataprocess.py`


* PyTorch (structureSplit)
  * `model.py`
  * `param.pth`
  * `class.txt`
  * `pre_dataprocess.py`
  * `post_dataprocess.py`

* MXNet
  * [ ] TODO

