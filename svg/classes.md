## Bundle
```mermaid
classDiagram
    JXS_Bundle --|> JXS_Bundle_Image
    JXS_Bundle --|> JXS_Bundle_Distro
    JXS_Bundle: model file
    JXS_Bundle: pre_process.py
    JXS_Bundle: post_process.py
    JXS_Bundle_Image: configs.json
    JXS_Bundle_Distro: distros.json
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