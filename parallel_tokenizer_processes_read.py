#!/usr/bin/env python
import subprocess
import math
import re
from collections import Counter
from multiprocessing import Pool

from nltk.stem import PorterStemmer

ps = PorterStemmer()
find_words_re = re.compile(r'''([a-zA-Z]+([^a-zA-Z\s]+[a-zA-Z]+)?)''')

def get_filename_generator():
    files = subprocess.check_output(
        "ls -1 /Users/mica/java/46b/tests/final/assignment/enron_with_categories/1/*.txt",
        shell=True,
    ).decode().strip().split('\n')
    for file in files:
        yield file

def get_contents(file):
    lines = list()

    with open(file, 'r') as fr:
        content = fr.read()

    for content_part in content.split('----------------------'):
        if content_part.startswith(' Forwarded'):
            continue
        # longest line was <70, so consider that it's not human-written text
        if max(map(len, content_part.split('\n'))) < 70:
            continue
        if 'Message-ID' in content_part:
            continue
        if 'From: ' in content_part:
            continue
        capturing = False
        for line in content_part.split('\n'):
            if capturing:
                lines.append(line)
            elif line.startswith('Subject:'):
                capturing = True
                continue

    return '\n'.join(lines)

def get_contents_simple():
    yield 'the cat sang'
    yield 'the dog sang'
    yield 'the the the'

def process_contents(filename, word_to_index):
    """
    input:
        content: "the cat sang"
        word_to_index: {'the': 1}
    output:
        found_indices: set([1])
        new_found_words: {cat, sang}
    """
    new_found_words = set()
    found_indices = set()
    wordcount = 0

    content = get_contents(filename)

    for m in find_words_re.finditer(content):
        wordcount += 1
        word = ps.stem(m.group(1).lower())
        word_index = word_to_index.get(word, None)
        if word_index is not None:
            found_indices.add(word_index)
        else:
            new_found_words.add(word)
    return found_indices, new_found_words, wordcount

def update_documents_per_term(new_found_words, word_to_index, foundword_indices, documents_per_term, i):
    for word in new_found_words:
        # word_to_index = {'a': 1, 'banana': 2}
        index = word_to_index.get(word, None)
        if index is not None:
            foundword_indices.add(index)
        else:
            # word_to_index['cheese'] = 3
            word_to_index[word] = i
            # foundword_indices.add(3)
            foundword_indices.add(i)
            i += 1

    # e.g. (this example uses strings as keys instead of
    # their integer index counterparts, so as to improve readability):
    # {'a': 1, 'dog': 2}.update({'dog', 'banana'})
    # -> {'a': 1, 'dog': 3, 'banana': 1}
    documents_per_term.update(foundword_indices)
    return i


def create_new_worker(filename, word_to_index, pool, workers):
    had_more_work = True
    workers.append(
        pool.apply_async(
            process_contents,
            (filename, word_to_index),
        )
    )

def run_tokenize(process_count=8):
    documents_per_term = Counter()
    total_document_count = 0
    word_to_index = dict()
    filename_generator = get_filename_generator()

    workers = list()
    pool = Pool(processes=process_count)

    have_more_work = True
    for i in range(process_count):
        try:
            filename = next(filename_generator)
        except StopIteration:
            have_more_work = False
            break
        create_new_worker(
            filename, word_to_index, pool, workers
        )
        total_document_count += 1

    i = 0
    total_word_count = 0
    while workers:
        worker = workers.pop(0)
        # this worker isn't done, so check the next worker
        if not worker.ready():
            workers.append(worker)
        # this worker is done, so process the results and create a new worker
        else:
            found_indices, new_found_words, wordcount = worker.get()

            total_word_count += wordcount
            i = update_documents_per_term(new_found_words, word_to_index, found_indices, documents_per_term, i)

            if have_more_work:
                try:
                    filename = next(filename_generator)
                    total_document_count += 1
                    create_new_worker(filename, word_to_index, pool, workers)
                except StopIteration:
                    have_more_work = False

    index_to_word = {v: k for k, v in word_to_index.items()}
    print('total_document_count:', total_document_count)
    print('total_word_count:', total_word_count)
    print('average words per document: {:.2f}'.format(total_word_count / total_document_count))
    # for word_index, count in documents_per_term.most_common():
    #     print((index_to_word[word_index], count, math.log(total_document_count/count)))

if __name__ == '__main__':
    run_tokenize(process_count=8)
