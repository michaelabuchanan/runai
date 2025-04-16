#!/bin/bash

pip install transformers accelerate bitsandbytes peft datasets einops torch
python ./runai-llm-train.py
