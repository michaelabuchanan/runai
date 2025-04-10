# -*- coding: utf-8 -*-
"""intro_to_llm_v3.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1cEhF9kiOdavbdqOdcsdossjYh7TExlzs

#**Introduction to Large Language Models**
### *Michaela Buchanan - Mark III Systems*

---

In this notebook we will be looking at using a LLM for inference as well as finetuning a LLM for a specific task. Please note that these are large models we are dealing with so downloading and training these models will take several hours.

Imports for all the code are below. Please run first before anything else!
"""

!pip install -q transformers accelerate bitsandbytes peft datasets einops torch

import torch
from transformers import AutoTokenizer, FalconForCausalLM, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForLanguageModeling
import transformers
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset, Dataset

!git clone https://github.com/michaelabuchanan/llm_education_session_lora.git

"""---

###Inference with Falcon-7B

We are going to start by using `Falcon-7B` to perform inference on some prompts we come up with. This will demonstrate how you can use Hugging Face's Transformers library to easily pull down and start using a model. The documentation for the model is [linked here](https://huggingface.co/ybelkada/falcon-7b-sharded-bf16). This is not the original version of Falcon-7B. Instead it's a sharded version, which means the files for the model are broken up into smaller pieces. Trying to load the original Falcon-7B model would cause us to run out of system RAM in our Google Colab instance.

You may be wondering how we are going to load and finetune a model with 7 billion parameters using only the T4 GPU provided by the free tier of Google Colab. A T4 GPU has 16GB of GPU RAM which may seem like a lot but to load a 7 billion parameter model at full precision one would have to use at least 28 GB of GPU memory, or almost twice what we have available to us.

To make this workshop happen we will be using the methodology outlined in the paper *QLoRA: Efficient Finetuning of Quantized LLMs* [linked here](https://arxiv.org/abs/2305.14314). It boils down to using reduced precision for our parameters which means we will need significatly less GPU RAM to load the model. In our case we are going to reduce the parameters from 16 bit precision to 4 bit precision, which means we will need appoximately 1/4 the GPU RAM to load our model. This will allow us to use this model for inference with the T4 GPU available to us.

Notice the `model` variable in the code cell below. If you download this notebook to run somewhere with more computionatonal resources or upgrade to Colab's Pro tier you can change the model specified in the variable to use other text-generation models available on Hugging Face. In our case we are using Falcon-7B-Instruct but are using a sharded version of the model rather than the original one linked above. This helps keep us from running out of disk system RAM as we load in the model by spliting it up into smaller pieces.

The first step is to create our tokenizer so that we can feed our input into the model. Remember that we can't just pass a query into the model, it has to be converted into a numeric format first. To create our tokenizer we are going to use the AutoTokenizer class from HuggingFace. [Visit this link](https://huggingface.co/docs/transformers/v4.32.0/en/model_doc/auto#transformers.AutoTokenizer) to see the documentation for this class. We can pass the name of the model we would like to use to AutoTokenizer and it will automatically set up the tokenizer we need to interact with the model.
"""

model = "ybelkada/falcon-7b-sharded-bf16"

tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

"""Next we need to set up our BitsAndBytesConfig. We are using the BitsAndBytes library to make our parameter precision changes so that we can load our 7 billion parameter model without running out of GPU RAM. As you can see below we are loading the model in 4 bit format by using the load_in_4bit parameter."""

bb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

"""Below you can see the code for actually loading our model. We use another Auto class from HuggingFace to do this, this time AutoModelForCausalLM. We give it the name of the model we want to load and the BitsAndBytes configuration we just defined. When you run this code cell you should see it load in the sharded portions of the model which will take a while to download and load into memory."""

falcon_model = FalconForCausalLM.from_pretrained(
    model,
    quantization_config=bb_config,
    use_cache=False,
    low_cpu_mem_usage=True
)

"""Now that we have our model loaded let's do some inference examples with it. Below you can see that we have a prompt for our model in the text variable, in this case a question about the national bird of the United States. We need to use our tokenizer to convert our prompt into something we can feed the model. Then we can use the generate funtion to give our model our tokenized prompts and save the output as outputs. The printed results say that the national bird is a bald eagle which is correct."""

text = "Question: What is the national bird of the United States? \n Answer: "

inputs = tokenizer(text, return_tensors="pt").to("cuda:0")
outputs = falcon_model.generate(input_ids=inputs.input_ids, max_new_tokens=10, pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

"""Below is another similar example with a new prompt. Feel free to change the prompt to experiment with the model. Creating a good prompt is more of an art than a science and you may find that small differences in the way you phrase a question can have large impacts on how the model interprets it and responds."""

text2 = "How do I make teriyaki sauce?"

inputs = tokenizer(text2, return_tensors="pt").to("cuda:0")
outputs = falcon_model.generate(input_ids=inputs.input_ids, max_new_tokens=50, pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

"""Now let's change things up a bit. For the finetuning portion of this workshop we are going to be using the MedText dataset. This dataset contains blurbs of patient symptoms and then an associated diagnosis and action plan to treat the symptoms. The hope with our finetuning is that we can give the model a description of symptoms as the prompt and then produce a reasonable response as output. Let's test our current model to see how it performs on this task as a baseline. Below you can see one of the entries in the MedText dataset as our prompt.  """

text3 = "A 25-year-old female presents with swelling, pain, and inability to bear weight on her left ankle following a fall during a basketball game where she landed awkwardly on her foot. The pain is on the outer side of her ankle. What is the likely diagnosis and next steps? "

inputs = tokenizer(text3, return_tensors="pt").to("cuda:0")
outputs = falcon_model.generate(input_ids=inputs.input_ids, max_new_tokens=100, pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

"""We can see that the response from our model is reasonable but not in the format or detail that we are hoping for. It just generate a list of possible conditions that could be associated with the symptoms in our prompt. Keep this response in mind as we will compare it to the output generated by our finetuned model at the end of this workshop.

---


###Finetuning on the MedText Dataset

As promised we are going to finetune our Falcon model using the MedText dataset. The first step is going to be to define some arguments for training. Below you can see the configuration we are going to be using for this which is saved as training_args.
"""

training_args = TrainingArguments(
    output_dir="./finetuned_falcon",
    eval_strategy="epoch",
    learning_rate=2e-5,
    weight_decay=0.01,
    fp16 = True,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=1,
    logging_steps=1,
    num_train_epochs=1,
    optim = "paged_adamw_8bit",
    report_to="none"
)

"""We are going to be using the peft library to make finetuning possible on the hardware we have in this notebook. What this will allow us to do is finetune on some "adapter" parameters that will be incorperated into our existing model rather than attempting to finetune all 7 billion parameters we already have. This will make training much more feasible compuationally and also keep the model from "forgetting" things it already knows in the finetuning process. Below you can see the configuration we are going to use to make this happen. We use that configuration along with the get_peft_model method to generate a new model that has adapters we can finetune, which we store into the variable lora_model."""

print(falcon_model)

falcon_model.gradient_checkpointing_enable()
falcon_model = prepare_model_for_kbit_training(falcon_model)

lora_config = LoraConfig(
    r=4,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "query_key_value",
        "dense",
        "dense_h_to_4h",
        "dense_4h_to_h",
    ]
)

lora_model = get_peft_model(falcon_model, lora_config)

"""The function below counts and prints out  the number and percentage of parameters we will be using to train compared to the total number of parameters in the model. You should see that we will be training only ~0.12% of the total parameters which tells us our LoRa setup was successful."""

lora_model.print_trainable_parameters()

"""Now we need our dataset that we are going to use for finetuning. We are going to use MedText which is hosted on the HuggingFace Hub. This means we can use the load_dataset function to import our dataset as seen below."""

dataset = load_dataset("BI55/MedText", split="train")

"""For finetuning we are going to combine our prompts and responses. Below you can see where we create a Pandas DataFrame from our dataset, grab the Prompt and Completion columns, and combine both in a new Info column."""

import pandas as pd

df = pd.DataFrame(dataset)
prompt = df.pop("Prompt")
comp = df.pop("Completion")
df["Info"] = prompt + "\n" + comp

"""A lot of the work that goes into finetuning is preprocessing the data you wish to feed the model. Not only do we need to run all our data through our tokenizer, but we also need to ensure that we keep the dimensions of our data in line with what the model expects. Below you can see the function I used to handle the tokenization and returning the tokenized results. This function is based on the tokenizing function writted by Harveen Singh Chanda which is linked in the comment below."""

# https://www.kaggle.com/code/harveenchadha/tokenize-train-data-using-bert-tokenizer
def tokenizing(text, tokenizer, chunk_size, maxlen):
    input_ids = []
    tt_ids = []
    at_ids = []
    tokenizer.pad_token = tokenizer.eos_token

    for i in range(0, len(text), chunk_size):
        text_chunk = text[i:i+chunk_size]
        encs = tokenizer(
                    text_chunk,
                    max_length = 2048,
                    padding='max_length',
                    truncation=True,
                    )

        input_ids.extend(encs['input_ids'])
        tt_ids.extend(encs['token_type_ids'])
        at_ids.extend(encs['attention_mask'])

    return {'input_ids': input_ids, 'token_type_ids': tt_ids, 'attention_mask':at_ids}

"""Now we can use this function to preprocess our data. We pass the Info column we created earlier into this function as a list along with the tokenizer we intilalized ealier and receive tokens as output. We can use the HuggingFace Datasets object to easily create a dataset from these tokens and then split the dataset into train and test subsets."""

tokens = tokenizing(list(df["Info"]), tokenizer, 256, 2048)
tokens_dataset = Dataset.from_dict(tokens)
split_dataset = tokens_dataset.train_test_split(test_size=0.2)
split_dataset

"""We now only need one more piece before we can start training - the Trainer itself. Below you can see that we initialize the `trainer` by giving it the LoRA model we created, our training argument configuration, and our dataset."""

trainer = Trainer(
    model=lora_model,
    args=training_args,
    train_dataset=split_dataset["train"],
    eval_dataset=split_dataset["test"],
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

"""If you would like to perform the finetuning in this notebook go ahead and uncomment the two lines below. These will perform the training and then save the low ranking adapters to the `finetuned_falcon` directory. However note that training will take about 2-4 hours. Therefore this notebook is set up to use already finetuned low ranking adapters from a previous finetuning run. This allows us to skip the training time and see how you would utilize the resulting files to reinstanciate the model for inference. These already finetuned files are cloned from a GitHub repository in the first cell of this notebook. To use the pretrained files you should not have to change anything in this notebook."""

# trainer.train()
# trainer.model.save_pretrained("./finetuned_falcon")

"""---


###Testing the Finetuned Model

Now that our finetuning is complete it's time to see if it gives a better response to the MedText data than it did before. We first need to load in our finetuned model as seen below.
"""

from peft import PeftConfig, PeftModel

config = PeftConfig.from_pretrained('./llm_education_session_lora')

# if using already finetuned files
finetuned_model = PeftModel.from_pretrained(falcon_model, './llm_education_session_lora')

# comment out line 6 and uncomment this if you are finetuning in this notebook
# finetuned_model = PeftModel.from_pretrained(falcon_model, './finetuned_falcon')

"""Then we will do inference just like we did before with the same prompt used previously."""

text4 = "A 25-year-old female presents with swelling, pain, and inability to bear weight on her left ankle following a fall during a basketball game where she landed awkwardly on her foot. The pain is on the outer side of her ankle. What is the likely diagnosis and next steps?"

inputs = tokenizer(text4, return_tensors="pt").to("cuda:0")
outputs = finetuned_model.generate(input_ids=inputs.input_ids, max_new_tokens=75, pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

"""As you can see the response is now much more similar to the MedText responses. Not only are the recommendations the model gives reasonable but the way the responses are written are also much more cohesive and professional than the list it gave us before. This shows how finetuning can be used to change the behavior of a LLM pretty dramatically.

---

###Helpful Resources for Further Study

As mentioned in the lecture portion of this workshop, we did not have time to cover many important aspects of how LLMs work. Below I have links to resources I found useful in understanding how Transformers work as well as other concepts mentioned in this session.

Papers:
*   8 Things to Known about LLMs paper: https://arxiv.org/abs/2304.00612
*   Attention is All You Need (original transformers paper): https://arxiv.org/abs/1706.03762
*   LoRA: Low-Rank Adaptation of Large Language Models: https://arxiv.org/abs/2106.09685
*   QLoRA: Efficient Finetuning of Quantized LLMs: https://arxiv.org/abs/2305.14314

Blogs:
*   Blog explaining building a Transformer model from scratch: https://peterbloem.nl/blog/transformers
*   Blog on Bits and Bytes: https://huggingface.co/blog/hf-bitsandbytes-integration
*   Hugging Face's Blog on Falcon: https://huggingface.co/blog/falcon
*   Using LoRa for finetuning: https://dataman-ai.medium.com/fine-tune-a-gpt-lora-e9b72ad4ad3
*   LoRa Parameter Overview: https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms


YouTube videos:
*   University of Waterloo lecture on Attention and Transformers: https://www.youtube.com/watch?v=OyFJWRnt_AY
*   Attention is All You Need paper explanation: https://www.youtube.com/watch?v=w76Dpp7b3B4
"""