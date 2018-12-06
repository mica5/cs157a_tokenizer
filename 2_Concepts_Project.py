#!/usr/bin/env python
import os
import re
from collections import Counter
import subprocess

import spacy
dictwords = set()

with open('/usr/share/dict/words', 'r') as fr:
    for line in fr:
        dictwords.add(line.strip().lower())

nlp = spacy.load('en')

files = subprocess.check_output('ls -1 presentation-2018-12-04', shell=True).decode().strip().split('\n')
files = [os.path.join('presentation-2018-12-04', f) for f in files]

# can consider only directly-adjacent words, or skip grams. currently it's just considering directly adjacent words.
%%time
c = Counter()
for file in files:
    with open(file, 'r', errors='ignore') as fr:
        for sentence in re.split(r'\.+', fr.read().lower()):
            tokens = nlp(sentence.strip())
            for i in range(len(tokens)-1):
                t1 = tokens[i]
                if (not t1.text.strip()) or t1.is_punct:
                    continue

                t2 = tokens[i+1]
                if (not t2.text.strip()) or t2.is_punct:
                    continue

                # make sure at least one of the words isn't a stopword
                if False not in (t1.is_stop, t2.is_stop):
                    continue

                # make sure we don't just have a couple letters or empty strings
                if len(t1.text) < 2 and len(t2.text) < 2:
                    continue

                # make sure at least one word is a dictword
                if t1.text not in dictwords and t2.text not in dictwords:
                    continue

                c[(t1.text, t2.text)] += 1


print(c.most_common(500))

for l in c.most_common():
    t, c = l
    if 'neural' in t:
        print(l)
