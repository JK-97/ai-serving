# JX Serving GRPC Interface

## Interface List
* common.proto
* backend.proto
* connectivity.proto
* exchange.proto
* inference.proto
* model.proto


## `common.proto`
This interface is used to provide some common request or response information
#### PingRequest
Field | Type | Description
-|-|-
client | string | a signature of client
#### ResultReply
Field | Type | Description
-|-|-
code | uint32 | error code
msg | string | return message (if available)


## `backend.proto`
This interface is used to operate backends of current node
#### SupportedReply
Field | Type | Description
-|-|-
support | string | support backends
#### BackendInfo
Field | Type | Description
-|-|-
bid | string | backend id
impl | string | backend implementation (e.g. `tensorflow.frozen`)
storage | string | preserved, not use
preheat | string | preserved, not use
batchsize | uint32 | inference batch size
inferprocnum | uint32 | inference process number
exporter | string | preserved, not use (e.g. `redis`)
backendext | string | preserved
#### BackendStatus
Field | Type | Description
-|-|-
info | **BackendInfo** | backend information
status | string | current backend status
msg | string | error message
#### BackendList
Field | Type | Description
-|-|-
backends | *repeated* **BackendStatus** | backends status list
#### LoadRequest
Field | Type | Description
-|-|-
bid | string | backend id
model | **ModelInfo** | model infomation
encrypted | uint32 | encrypted model, either `1` or `0`, otherwise regard as `0`
a64key | string | if encrypted model, provide access code
pvtpth | string | if encrypted model, provide decrypt private key path
#### FullLoadRequest
Field | Type | Description
-|-|-
backend | **BackendInfo** | backend infomation
model | **ModelInfo** | model infomation
encrypted | uint32 | encrypted model, either `1` or `0`, otherwise regard as `0`
a64key | string | if encrypted model, provide access code
pvtpth | string | if encrypted model, provide decrypt private key path

### `ListSupportedType (PingRequest) returns (SupportedReply)`
* supported backend types of current node
```python
response = stub.ListSupportedType(c_pb2.PingRequest(client="test.client"))
```

### `ListRunningBackends (PingRequest) returns (BackendList)`
* list all running backends on this node
```python
response = stub.ListRunningBackends(c_pb2.PingRequest(client="test.client"))
```

### `InitializeBackend (BackendInfo) returns (ResultReply)`
* create a new backend, only `btype` is needed
```python
backend_info = {'impl': "tensorflow.frozen"}
response = stub.InitializeBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
```

### `ListBackend (BackendInfo) returns (BackendStatus)`
* return the status of a specific running backend
```python
backend_info = {'bid': return_bid}
response = stub.ListBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
```

### `ReloadModelOnBackend (LoadRequest) returns (ResultReply)`
* reload a specific model on given backend
```python
load_info = {
  'bid': "0",
  'model': {
      'implhash': "226a7354795692913f24bee21b0cd387",
      'version': "1",
  },
  'encrypted': 0,
  'a64key': "",
  'pvtkey': "",
}
response = stub.ReloadModelOnBackend(ParseDict(load_info, be_pb2.LoadRequest()))
```

### `TerminateBackend (BackendInfo) returns (ResultReply)`
* terminate a created backend
```python
backend_info = {'bid': return_bid}
response = stub.TerminateBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
```

### `CreateAndLoadModel (FullLoadRequest) returns (ResultReply)`
* try to create a new backend and try to load a specific model to this created backend, if failed, automatically delete this backend
```python
load_info = {
  'backend': {'impl': "tensorflow.frozen"},
  'model': {
      'implhash': "226a7354795692913f24bee21b0cd387",
      'version': "1",
  },
  'encrypted': 0,
  'a64key': "",
  'pvtkey': "",
}
response = stub.CreateAndLoadModel(ParseDict(load_info, be_pb2.FullLoadRequest()))
```

## `connectivity.proto`
This interface is used check connectivity of current node
#### PingReply
Field | Type | Description
-|-|-
version | string | version
#### ResourceReply
Field | Type | Description
-|-|-
cpu | string | cpu resource quota
mem | string | memory recource quota
gpu | string | gpu resource quota
dsk | string | disk resource quota

### `Ping (PingRequest) returns (PingReply)`
* ping current node
```python
response = stub.Ping(c_pb2.PingRequest(client="client"))
```
### `ListNodeResources (PingRequest) returns (RunningReply)`
* list all resources quota of current node
```python
response = stub.ListNodeResources(c_pb2.PingRequest(client="client"))
```

## `exchange.proto`
This interface is used to exchange binary file between server and client
#### Block
Field | Type | Description
-|-|-
index | uint64 | block id
hash | string | hash content
block | bytes | bytes data
#### BinData
Field | Type | Description
-|-|-
uuid | string | uuid of exchanged file
hash | string | hash content of exchanged file
size | uint64 | size of exchagned file
pack | **Block** | pack block

### `DownloadBin (stream BinData) returns (stream BinData)`
* download binary file from remote node
```python
def bin_request(bin_list):
    for b in bin_linst:
        yield b

response = stub.DownloadBin(bin_request([e_pb2.BinData(uuid="a1b2c3")]))
bin_blob = []
for r in response:
    bin_blob.append(r.pack.block)
with open("filename", "ab") as dump:
    for bb in bin_blob:
        dump.write(bb)
```
### `UploadBin (stream BinData) returns (stream BinData)`
* upload binary file to remote node
```python
def bin_response(bin_list):
    for i in range(len(bin_list)):
        yield e_pb2.BinData(
            pack=e_pb2.Block(
                index=i,
                block=bin_list[i],
            ))

bin_blob = []
with open("filename", "rb") as f:
    blob = f.read(2*1024*1024)
    while blob != b"":
        bin_blob.append(blob)
        blob = f.read(chunk_size)

responses = stub.UploadBin(bin_response(bin_blob))
```


## `inference.proto`
This interface is used to inference images/videos locally or remotely

#### InferRequest
Field | Type | Description
-|-|-
bid | string | backend id
uuid | string | provide a uuid for this inference, use this uuid as key to get result
path | string | if inference locally, provide image storage path
type | string | if inference remotely, provide data type (e.g. `jpeg`)
base64 | string | if inference remotely, contain image data

### `InferenceLocal (InferRequest) returns (ResultReply) {}`
* inference image locally
```python
auuid = str(uuid.uuid4())
infer = {
    'bid': "0",
    'uuid': auuid,
    'path': test_image,
}
response = stub.InferenceLocal(ParseDict(infer, inf_pb2.InferRequest()))

# when inference finished
rPool = redis.ConnectionPool(host="localhost", port=6379, db=5)
r = redis.Redis(host="localhost", port=6379, connection_pool=rPool)
print(r.get(auuid))
```

### `InferenceRemote (InferRequest) returns (ResultReply) {}`
* inference image remotely
```python
infer = {
    'bid': "0",
    'uuid': auuid,
    'type': "jpg",
    'base64': b64str_of_image,
}
response = stub.InferenceRemote(ParseDict(infer, inf_pb2.InferRequest()))
```


## `model.proto`
* This interface is used to operate models of current node
#### ModelInfo
Field | Type | Description
-|-|-
name | string | model name
labels | *repeated* string | labels of model
bundle | string | bundle_id (required while uploading)
head | string | algorithm head (e.g. `YOLO`)
bone | string | algorithm backbone (e.g. `mobilenet`)
impl | string | implementation framework (e.g. `tensorflow.frozen`)
implhash | string | hash value of labels, head, bone, impl
version | string | model version
threshold | *repeated* string | threshold list (notice: this is *[string,]* type)
mapping | *repeated* string | mapping label list
modelext | string | extra data for specific model, (e.g. tensor vector)
disthash | string | hash value of threshold and mapping
#### message ModelList 
Field | Type | Description
-|-|-
list | *repeated* **ModelInfo** | multiple pieces of model information

### `ListModels (PingRequest) returns (ModelList) {}`
* list stored models of current node
```python
response = stub.ListModels(c_pb2.PingRequest(client="test.client"))
```

### `CreateModel (ModelInfo) returns (ResultReply) {}`
* create an empty model folder for developer
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  "version": "1",
}
response = stub.CreateModel(ParseDict(example_model, m_pb2.ModelInfo()))
```

### `DistroConfig (ModelInfo) returns (ResultReply) {}`
* distribute configs to a specific model
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  "version": "1",
  "implhash": "a1b2c3",
  "threshold": ["0.2", "0.2", "0.2"],
  "mapping": ["c0", "c1", "c2"],
}
response = stub.DistroConfig(ParseDict(example_model, m_pb2.ModelInfo()))
```

### `DeleteModel (ModelInfo) returns (ResultReply) {}`
* delete a specific model
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  "version": "1",
}
response = stub.DeleteModel(ParseDict(example_model, m_pb2.ModelInfo()))
```

### `ExportModelImage (ModelInfo) returns (ResultReply) {}`
* export a specific model
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  "version": "1",
}
response = stub.ExportModelImage(ParseDict(example_model, m_pb2.ModelInfo()))
```

### `ImportModelDistro (ModelInfo) returns (ResultReply) {}`
* import a specific model
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'bundle': bin_name,
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  'version': "1",
  'implhash': "a1b2c3",
  "threshold": ["0.2", "0.2", "0.2"],
  "mapping": ["d0", "d1", "d2"],
}    
response = stub.ImportModelDistro(ParseDict(example_model, m_pb2.ModelInfo()))
```

### `ImportModelDistroV2 (ModelInfoBrief) returns (ResultReply) {}`
* import a specific model
```python
example_model = {
  'name':   "test-model",
  'labels': ["c0", "c1", "c2"],
  'bundle': bin_name,
  'head': "YOLO",
  'bone': "mobilenet",
  'impl': "tensorflow.frozen",
  'fullhash': "a1b2c3-1",
  "threshold": ["0.2", "0.2", "0.2"],
  "mapping": ["d0", "d1", "d2"],
}    
response = stub.ImportModelDistroV2(ParseDict(example_model, m_pb2.ModelInfoBrief()))
```

### `CreateAndLoadModelV2 (FullLoadRequestV2) returns (ResultReply)`
* try to create a new backend and try to load a specific model to this created backend, if failed, automatically delete this backend
```python
load_info = {
  'backend': {'impl': "tensorflow.frozen"},
  'model': {
      'fullhash': "226a7354795692913f24bee21b0cd387-1",
  },
  'encrypted': 0,
  'a64key': "",
  'pvtkey': "",
}
response = stub.CreateAndLoadModelV2(ParseDict(load_info, be_pb2.FullLoadRequestV2()))
```
