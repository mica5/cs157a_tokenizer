#!/usr/bin/env python
import os
import re
from collections import Counter
import subprocess

import spacy
dictwords = set()

this_dir = os.path.dirname(os.path.abspath(__file__))  #set directory
words_file = os.path.join(this_dir, 'words')           
with open(words_file, 'r') as fr:
    for line in fr:
        dictwords.add(line.strip().lower())            #remove whitespace

nlp = spacy.load('en')  
#put your directory name in place of mine...
dirName = "C:/Users/jaked/Downloads/cs157a_tokenizer-master (1)/cs157a_tokenizer-master/myfiles"
#helper method for use in Unix/Windows:
def getLocalFiles():
   list_files=os.listdir(dirName)
   file_objs=list()
   for filename in list_files:
       fullPath=dirName + '/' + filename
       file_objs.append(fullPath)
   return file_objs

files = getLocalFiles()
# can consider only directly-adjacent words, or skip grams. currently it's just considering directly adjacent words.
c = Counter()
for file in files:
    with open(file, 'r', errors='ignore') as fr:
        for sentence in re.split(r'\.+', fr.read().lower()):  #split between periods to get sentences
            tokens = nlp(sentence.strip())  #strip the sentence of whitespace
            for i in range(len(tokens)-1):  
                t1 = tokens[i]
                if (not t1.text.strip()) or t1.is_punct:  #if t1.text is just whitespace or is a punctuation
                    continue

                t2 = tokens[i+1]
                if (not t2.text.strip()) or t2.is_punct:  #if t2.text is just whitespace or is a punctuation
                    continue

                # make sure at least one of the words isn't a stopword
                if False not in (t1.is_stop, t2.is_stop):  #if one or both of the words are not in the stopword list is false
                    continue

                # make sure we don't just have a couple letters or empty strings
                if len(t1.text) < 2 and len(t2.text) < 2: #if the length of t1's and t2's words are both less than 2
                    continue

                # make sure at least one word is a dictword
                if t1.text not in dictwords and t2.text not in dictwords: #if  t1's and t2's words are not a dictionary defined word
                    continue

                c[(t1.text, t2.text)] += 1  #add 1 to counter


print(c.most_common(500))  #prints 500 most valuable 2-Concepts
