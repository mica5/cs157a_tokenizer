#!/usr/bin/env python3
"""2-concepts

Version 0.1
2018-11
Team Titans
"""
import os
import re
from collections import Counter
import subprocess
import argparse

import spacy

def run_main():
    args = parse_cl_args()

    files = args.files

    dictwords = set()

    this_dir = os.path.dirname(os.path.abspath(__file__))
    words_file = os.path.join(this_dir, 'words')
    with open(words_file, 'r') as fr:
        for line in fr:
            dictwords.add(line.strip().lower())

    nlp = spacy.load('en')

    # can consider only directly-adjacent words, or skip grams. currently it's just considering directly adjacent words.
    # %%time
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

    success = True
    return success

def parse_cl_args():

    argParser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    argParser.add_argument('files', nargs='+')

    args = argParser.parse_args()
    return args


if __name__ == '__main__':
    success = run_main()
    exit_code = 0 if success else 1
    exit(exit_code)

