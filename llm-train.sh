#!/bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch
pip uninstall -y apex
python /workspace/gitdata/runai/runai-llm-train.py
