1. Deploy 

`cd src && pip3 install -r requirements.txt`

2. Run 

```
cd src && python3 run.py
```

* Run with options
  * format: `python3 run.py [options]`
  * `--debug`, enter debug mode, print more messages
  * `--profile`, enter profile mode, print profile messages



3. API

```
    POST  /api/v1alpha/detect {
                        "path": "/absolute/path/of/image"}

Response: {"result": "[['ai_prediction', 'defined by model', ...]]"}
```

```
    GET   /api/v1alpha/switch

Response: {"model": "model name", 
           "status": "status of loading process",
           "error": "error message when encounter problem"}
```

```
    POST  /api/v1alpha/switch {
                        "model": "model name", 
                        "mode": "model type", // this will either be "frozen" or "unfrozen"
                        "preheat": "whether to preheat session"}  // this will always be True

Response: {"result": "result of switching caller"}, this will either be "succ" or "fail"
```

* See example under `test/test_runSession`


4. How to Serve an AI model

* First, change `model_path` and `preheat_image_path` in `settings.py`

Prepare a directory that contains following five things, then this model can be served:

* For frozed model

* 5 things need to prepare
  1. Frozed model.pb file
  2. class.txt
  3. tensor.json
  4. pre_dataprocess.py
  5. post_dataprocess.py


* Fast build AI model
  //TODO(arth)
