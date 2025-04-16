#!/bin/bash

pip install --no-cache-dir --upgrade transformers accelerate bitsandbytes peft datasets einops torch==1.7.0
python /workspace/gitdata/runai/runai-llm-train.py
