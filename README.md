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
    POST  /api/v1/detect {"image_path": "/absolute/path/of/image"}

Response: {"result": "[['ai_prediction', 'defined by model', ...]]"}
```

* See example under `test/test_runSession`


4. How to Serve an AI model

Prepare a directory that contains following five things, then this model can be served:

* Frozed `.pb` file, normally named as `model.pb`

* 5 things need to prepare
  1. Frozed PB file
  2. class.txt
  3. tensor.json
  4. pre_dataprocess.py
  5. post_dataprocess.py


5. Fast build AI model
