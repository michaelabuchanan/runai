#!/bin/bash

pip install --no-cache-dir --upgrade transformers accelerate bitsandbytes peft datasets einops torch
python /workspace/gitdata/runai/runai-llm-train.py
