#! /bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch
chmod +x /home/runai-llm-train.py
python /home/runai-llm-train.py
