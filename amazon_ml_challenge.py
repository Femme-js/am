# -*- coding: utf-8 -*-
"""Amazon ML challenge.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N1alNnjtgDQ2e8ukbNYA085YixTm9NGN
"""

# Commented out IPython magic to ensure Python compatibility.
from IPython.core.debugger import set_trace

# %load_ext nb_black

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import time
import csv
plt.style.use(style="seaborn")
# %matplotlib inline

import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.layers.recurrent import LSTM, GRU
from keras.layers.core import Dense, Activation, Dropout
from keras.layers import GlobalMaxPooling1D, Conv1D, MaxPooling1D, Flatten, Bidirectional, SpatialDropout1D
from keras.initializers import Constant
from keras.utils import np_utils
from keras.optimizers import Adam
from keras.layers.embeddings import Embedding
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

train = pd.read_csv('/content/drive/MyDrive/train.csv', escapechar = "\\",quoting=csv.QUOTE_NONE)

train['DESCRIPTION'] = train['DESCRIPTION'].fillna('a')
train['TITLE'] = train['TITLE'].fillna('a')
train['BULLET_POINTS'] = train['BULLET_POINTS'].fillna('a')
train['BRAND'] = train['BRAND'].fillna('a')
train.head()

train["FEATURE"] = train["TITLE"] + train["DESCRIPTION"] + train['BULLET_POINTS'] + train['BRAND']

train.drop(["TITLE","DESCRIPTION",'BULLET_POINTS','BRAND'], axis = 1, inplace= True)
train.head()

import string


def remove_punct(text):
    table = str.maketrans("", "", string.punctuation)
    return text.translate(table)

train["FEATURE"] = train.FEATURE.map(lambda x: remove_punct(x))

from nltk.corpus import stopwords

stop = set(stopwords.words("english"))


def remove_stopwords(text):
    text = [word.lower() for word in text.split() if word.lower() not in stop]

    return " ".join(text)

train["FEATURE"] = train["FEATURE"].map(remove_stopwords)

train.FEATURE

groups = train.groupby('BROWSE_NODE_ID').count()

id_use = list(groups[groups['FEATURE']>15000].index)

trainA = train[train['BROWSE_NODE_ID'].isin(id_use)]
print(len(train))
print(len(trainA))

nltk.download('wordnet')

def getLemmText(text):
 tokens=word_tokenize(text)
 lemmatizer = WordNetLemmatizer()
 tokens=[lemmatizer.lemmatize(word) for word in tokens]
 return ' '.join(tokens)
trainA['FEATURE'] = list(map(getLemmText,trainA['FEATURE']))

def getStemmText(text):
 tokens=word_tokenize(text)
 ps = PorterStemmer()
 tokens=[ps.stem(word) for word in tokens]
 return ' '.join(tokens)
trainA['FEATURE'] = list(map(getStemmText,trainA['FEATURE']))

label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(trainA.BROWSE_NODE_ID.values)
len(np.unique(labels))

len(trainA)

xtrain, xtest, ytrain, ytest = train_test_split(trainA.FEATURE.values, labels, 
 random_state=42, 
 test_size=0.1, shuffle=True)

from tqdm import tqdm
embeddings_index = {}
f = open('/content/drive/MyDrive/glove.twitter.27B.25d.txt',encoding='utf8')
for line in tqdm(f):
 values = line.split()
 word = values[0]
 coefs = np.asarray(values[1:], dtype='float32')
 embeddings_index[word] = coefs
f.close()
print('Found %s word vectors.' % len(embeddings_index))

VOCABULARY_SIZE = 2000
MAX_LENGTH = 60

tokenizer = Tokenizer(num_words=VOCABULARY_SIZE)
tokenizer.fit_on_texts(list(xtrain) + list(xtest))

xtrain_sequence = tokenizer.texts_to_sequences(xtrain)
xtest_sequence = tokenizer.texts_to_sequences(xtest)

xtrain_padding = pad_sequences(xtrain_sequence, maxlen=MAX_LENGTH)
xtest_padding = pad_sequences(xtest_sequence, maxlen=MAX_LENGTH)
word_index = tokenizer.word_index

embedding_matrix = np.zeros((len(word_index) + 1, 25))
for word, i in tqdm(word_index.items()):
 embedding_vector = embeddings_index.get(word)
 if embedding_vector is not None:
  embedding_matrix[i] = embedding_vector

model = Sequential()
model.add(Embedding(len(word_index) + 1,
 25,
 weights=[embedding_matrix],
 input_length=MAX_LENGTH,
 trainable=False))
model.add(SpatialDropout1D(0.3))
model.add(Bidirectional(LSTM(100, dropout=0.3, recurrent_dropout=0.3)))
model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.8))
model.add(Dense(100, activation='relu'))
model.add(Dropout(0.8))
model.add(Dense(21))
model.add(Activation('softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

ytrain_encode = np_utils.to_categorical(ytrain)
ytest_encode = np_utils.to_categorical(ytest)

history = model.fit(xtrain_padding, y=ytrain_encode, batch_size=512, epochs=5, verbose=1, validation_data=(xtest_padding, ytest_encode))

