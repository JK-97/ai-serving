## Bundle
```mermaid
classDiagram
    AIS_Bundle --|> AIS_Bundle_Image
    AIS_Bundle --|> AIS_Bundle_Distro
    AIS_Bundle: model file
    AIS_Bundle: pre_process.py
    AIS_Bundle: post_process.py
    AIS_Bundle_Image: configs.json
    AIS_Bundle_Distro: distros.json
```
## Memory
```mermaid
classDiagram
    GlobalMemory <-- Runtime
    GlobalMemory <-- dict_FGs
    GlobalMemory <-- dict_BEs
    GlobalMemory <-- dict_Ps
    GlobalMemory <-- dict_Conns
    Runtime : PyObj codes
    Runtime : str dev_serial
    Runtime : bool debug
    Runtime : bool profile
    dict_FGs: [key]: bool
    dict_BEs: [key]: AbstractBackend
    dict_Ps: [key]: lambda
    dict_Conns: [key]: connections
    dict_BEs <-- BE1
    dict_BEs <-- BE2
```