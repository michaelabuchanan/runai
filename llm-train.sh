#!/bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch
python /workspace/gitdata/runai/runai-llm-train.py
