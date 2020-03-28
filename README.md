# AI-Serving

[Attention] This repo's git ignored all `*.c` file

[Attention] In some system, protobuf will fallback to pure python implementation, which is ***much slower***
* `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp` can help to solve this problem
* Please verify that: `run.py:L6` sets to a correct protocbuf implementation

[Attention] Currently only verified on `python3` environment


#### Introduction

* **AIServing OnBoard** is designed to:
  * provide an unified Deep Learning (DL) detection interface
  * a delegate agent of **AIServing Cloud**, under a distributed deployment

* Currently supported DL framework:
  * *Tensorflow*, [ ] *Tensorflow Serving*, [ ] *Tensorflow-Lite*
  * [ ] *PyTorch*
  * [ ] *RKNN*
  * [ ] *MXNet*


#### Components

* `src` stores all source files
* `build_release.py` and `setup.py` is used to build binary
* `CHANGELOG` is used to keep fixing, changing, adding features log
* `Dockerfile` is used to build containerize image
* `ld.conf` is used to link dynamic library inside container building


#### Installation

* [ ] Requirements (OutDated)
  * Depends on the backend you are using, install all
  * Ex1. Tensorflow on Jetson GPU
```
apt-get -y install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev
pip3 install -U numpy grpcio absl-py py-cpuinfo psutil portpicker six mock requests gast h5py astor termcolor protobuf keras-applications keras-preprocessing wrapt google-pasta
pip3 install tensorflow-estimator==1.13.0 tensorboard==1.13.0
pip3 install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v42 tensorflow-gpu==1.13.1+nv19.3
```

* Build for Release (This helps to protect source code)
  * `python build_release.py` (in some environment, it needs `python3 build_release.py`)
  * after above, all release binaries are stored in `release-pack`
  * ATTENTION: We noticed that generated binaries are highly related to the version of python that executed building command above, hence always use the same version of python to build or execute

* Deployment
  * Copy the whole `release-pack` folder to the path you want

* Deployment by Docker
  * [ ] TODO


#### Concept
* AIServing Model (JSM)
  * JSM is a folder that contains all information

* **AIServing** has the following concepts
  * For each inference, all data will pass through workflow shown as blow
    * Image -> Pre-DataProcess -> DL Backend -> Post-DataProcess
    * Here, Pre/Post-DataProcess are implemented by the model provider
  * Pre-DataProcess
    * `def pre_dataprocess(infer_data):`
    * `infer_data` comes from HTTP Restful request (`/api/v1alpha/detect`)
    * expect to return dictionary object which includes a data frame needed by DL framework
  * Post-DataProcess
    * `def post_dataprocess(pre_p, prediction, classes):`
    * `pre_p` is Pre-DataProcess result, `prediction` is DL inference result
    * `classes` is an array contains all classes supported by this DL model
    * expect to return dictionary object which includes a data frame that you want to return to actual users



#### Usage

* Config `settings.py`
  * set `storage`: path of a directory which stores all *JSM* bundle
  * set `preheat`: path of an image which is used to preheat nerual network
  * set `redis.host`: redis server host
  * set `redis.port`: redis server port, by default it is "6379"
  * other configurations need to check the specific list of each backend

* Prepare *JSM*
  * Copy *JSM* bundle to the `storage` path you set in `settings.py`
  * See more details in **Serving Bundle** section

* Run (w/ options) ***(Not Available after gRPC API checked-in)***
  * format: `python3 run.py [options]`
  * `--port`, run on a specific port, by default is `8080`
  * `--debug`, enable debug mode, print much more debug messages
  * `--profile`, enable profile mode, used to profile functions

* Call gRPC API
  * Please check `.proto` files stored in `src/serving/interface`

* Call HTTP Restful API ***(Deprecated)***
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
  bid:     "backend id"             # backend id, a new backend will be created if not given
  btype:   "backend type"           # backend type, must be given if a new backend need to create
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


#### Serving Bundle

* **AIServing** will automatically serving a model once this model is constrcuted with a conventional structure

* Tensorflow (Frozen)
  * `model_core`
  * `pre_dataprocess.py`
  * `post_dataprocess.py`
  * `distros.json`

