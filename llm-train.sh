#!/bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch==1.9.0
python /workspace/gitdata/runai/runai-llm-train.py
