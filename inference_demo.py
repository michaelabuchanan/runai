# https://colab.research.google.com/github/NVIDIA/NeMo/blob/stable/tutorials/nlp/Token_Classification_Named_Entity_Recognition.ipynb#scrollTo=DQhsamclRtxJ
from nemo.collections.nlp.models import TokenClassificationModel

queries = [
    'Jerry had appendicitis last week so I will not be going to the concert.',
    'While George was at the Walmart he read an article describing the dangers of Lyme disease.',
    'We bought four shirts from the Nvidia gear store in Santa Clara.',
    'Tony was just at the hospital and was diagnosed with diabetes'
]

print("\n" + str(TokenClassificationModel.list_available_models()) + "\n")

model = TokenClassificationModel.from_pretrained(model_name="ner_en_bert") 
results = model.add_predictions(queries)

print("\n")
for q, r in zip(queries, results):
    print("\nQUERY: " + q + "\nRESULT: " + r + "\n")