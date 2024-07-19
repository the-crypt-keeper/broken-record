#!/bin/bash

rm -rf build
git clone https://github.com/ggerganov/llama.cpp build
cd build
git apply ../fix-ignore-eos.patch
make LLAMA_CUDA=1 llama-cli -j
cd -