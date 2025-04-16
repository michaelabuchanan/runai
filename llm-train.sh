#!/bin/bash

python -m pip install --upgrade pip
pip install --no-cache-dir --upgrade transformers accelerate bitsandbytes==0.45.5 peft datasets einops
python /workspace/gitdata/runai/runai-llm-train.py
