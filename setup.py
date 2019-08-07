import sys
from distutils.core import setup
from Cython.Build import cythonize

srcs = []

with open("srcs.txt", "r") as f:
    srcs = eval(f.read().encode('utf-8'))

setup (ext_modules =
        cythonize(
            srcs,
            compiler_directives={'always_allow_keywords': True} ,
            language_level=3))
