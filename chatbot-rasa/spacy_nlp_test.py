import spacy
from spacy.lang.el.examples import  

nlp = spacy.load("el_core_news_md")
doc = nlp(sentences[0])
print(doc.text)
for token in doc:
    print(token.text, token.pos_, token.dep_,spacy.explain(token.pos_))
