#!/bin/bash

pip install transformers accelerate bitsandbytes==0.45.5 peft datasets einops torch==2.6.0
python /workspace/gitdata/runai/runai-llm-train.py
