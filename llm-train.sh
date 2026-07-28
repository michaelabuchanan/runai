#!/bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch torchao
# pip uninstall -y apex
python3 /workspace/runai/runai-llm-train.py --lr=$1
