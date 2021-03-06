#!/usr/bin/env python
"""Tokenizer

Runs in parallel, reads from local file system (but could easily
be modified to read from the internet, as there are already functions
for that).

Version 0.1
2018-09-20
Author: Mica Eldridge and Team Titans
"""
import subprocess
import math
import re
from collections import Counter
from multiprocessing import Pool
import urllib
from glob import glob
import os
import argparse

import requests
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer

# Create singleton porter stemmer
ps = PorterStemmer()

# Global regex to define a word - Only letters a-zA-z and internal hyphens
find_words_re = re.compile(
    r'('
        r'[-a-zA-Z]+'
        # r'('
        #     r'[^a-zA-Z\s]+'
        #     r'[a-zA-Z]+'
        # r')?'
    r')'
)

# Define multiple encodings to handle different file types
encodings = 'utf-8 ascii raw_unicode_escape windows-1252'.split()

def read_file(file):
    """ Read a file with varying encodings to until a valid reader can be established """
    for encoding in encodings:
        with open(file, 'r', encoding=encoding) as fr:
            try:
                return fr.read()
            except KeyboardInterrupt:
                raise
            except:
                continue
    # Failed to parse document with any encoding
    print("failed to read file '{}' with any of the given encodings".format(file))
    return

def get_file_or_dir_contents(files_or_dirs=['./documents']):
    for file_or_dir in files_or_dirs:
        if not os.path.isdir(file_or_dir):
            yield read_file(file_or_dir)
        else:
            for file in glob(os.path.join(file_or_dir, '*')):
                yield read_file(file)

def process_contents(content, word_to_index, document_id, word__idorstr__to_count):
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
    total_word_count_this_document = 0
    for m in find_words_re.finditer(content):
        total_word_count_this_document += 1
        word = ps.stem(m.group(1).lower())
        word_index = word_to_index.get(word, None)
        if word_index is not None:
            found_indices.add(word_index)
            word__idorstr__to_count.increment(word_index)
        else:
            new_found_words.add(word)
            word__idorstr__to_count.increment(word)

    return found_indices, new_found_words, total_word_count_this_document, document_id, word__idorstr__to_count

def update_documents_per_term(
        new_found_words, word_to_index, found_word__indices,
        word_index_to_doc_count_per_word, i, docid_to_word_indices, document_id,
    ):
    """
    found_word_indices is a set of the indices of the unique words
    that were found in a particular document. However, not all words
    had indices that corresponded to them at the time the worker
    was working, so this also takes the non-indexed words the worker
    found, gives them an index, and converts those from word counts to
    index counts.

    word_index_to_doc_count_per_word is {word index: number of documents the
    word appears in}.
    """
    for word in new_found_words:
        # word_to_index = {'a': 1, 'banana': 2}
        index = word_to_index.get(word, None)
        if index is not None:
            found_word__indices.add(index)
        else:
            # e.g. word_to_index['cheese'] = 3
            word_to_index[word] = index = i
            # e.g. found_word__indices.add(3)
            found_word__indices.add(i)
            i += 1
        if document_id in docid_to_word_indices:
            docid_to_word_indices[document_id].add(index)
        else:
            docid_to_word_indices[document_id] = {index}

    # e.g. (this example uses strings as keys instead of
    # their integer index counterparts, so as to improve readability):
    # {'a': 1, 'dog': 2}.update({'dog', 'banana'})
    # -> {'a': 1, 'dog': 3, 'banana': 1}
    word_index_to_doc_count_per_word.update(found_word__indices)
    return i


def create_new_worker(content_generator, word_to_index, pool, workers, document_id, word__idorstr__to_count):
    had_more_work = True
    try:
        content = next(content_generator)
    except StopIteration:
        had_more_work = False
        return had_more_work
    workers.append(
        pool.apply_async(
            process_contents,
            (content, word_to_index, document_id, word__idorstr__to_count),
        )
    )
    return had_more_work

class Word__idorstr__to_count:
    def __init__(self):
        self.word__idorstr__to_count = dict()
    def increment(self, word__idorstr):
        if word__idorstr not in self.word__idorstr__to_count:
            self.word__idorstr__to_count[word__idorstr] = 1
        else:
            self.word__idorstr__to_count[word__idorstr] += 1

class Documentid_to_word__idorstr__to_count:
    def __init__(self):
        self.documentid_to_word__idorstr__to_count = dict()
        self.docid_to_wordcount_this_doc = dict()

    def add_document(self, docid, word__idorstr__to_count, total_word_count_this_document):
        self.documentid_to_word__idorstr__to_count[docid] = word__idorstr__to_count.word__idorstr__to_count
        self.docid_to_wordcount_this_doc[docid] = total_word_count_this_document

    def increment(self, docid, word__idorstr):

        if docid not in self.documentid_to_word__idorstr__to_count:
            self.documentid_to_word__idorstr__to_count[docid] = dict()

        if word__idorstr in self.documentid_to_word__idorstr__to_count[docid]:
            self.documentid_to_word__idorstr__to_count[docid][word__idorstr] += 1
        else:
            self.documentid_to_word__idorstr__to_count[docid][word__idorstr] = 1

def run_tokenize(
    files_or_dirs, process_count=8, do_print=True, content_generator=get_file_or_dir_contents(),
    print_progress_int=-1,
):
    # word_index_to_doc_count_per_word is {word index: number of documents the word appears in}.
    word_index_to_doc_count_per_word = Counter()
    total_number_of_documents = 0
    word_to_index = dict()

    workers = list()
    pool = Pool(processes=process_count)

    word__idorstr__to_count = Word__idorstr__to_count()
    document_id = 0
    for i in range(process_count):
        had_more_content = create_new_worker(
            content_generator, word_to_index, pool, workers, document_id, word__idorstr__to_count
        )
        document_id += 1
        if not had_more_content:
            break
        total_number_of_documents += 1

    i = 0
    total_word_count_all_documents = 0
    docid_to_word_indices = dict()
    documentid_to_word__idorstr__to_count = Documentid_to_word__idorstr__to_count()
    while workers:
        worker = workers.pop(0)

        # this worker isn't done, so check the next worker
        if not worker.ready():
            workers.append(worker)
            continue

        # this worker is done, so process the results and create a new worker
        had_more_work = create_new_worker(content_generator, word_to_index, pool, workers, document_id, word__idorstr__to_count)
        if had_more_work:
            total_number_of_documents += 1

        if print_progress_int > 0 and total_number_of_documents % print_progress_int == 0:
            print("processed {} documents so far".format(total_number_of_documents))

        # found_indices is a set
        found_indices, new_found_words, total_word_count_this_document, document_id, word__idorstr__to_count = worker.get()
        documentid_to_word__idorstr__to_count.add_document(document_id, word__idorstr__to_count, total_word_count_this_document)

        total_word_count_all_documents += total_word_count_this_document
        i = update_documents_per_term(
            new_found_words, word_to_index, found_indices,
            word_index_to_doc_count_per_word, i, docid_to_word_indices,
            document_id,
        )

    # find a tokenizer to turn every file into a tuple of (token_id, token, document_id)
    index_to_word = {v: k for k, v in word_to_index.items()}
    token_id__token__document_id_results = list()
    for docid, word_indices in docid_to_word_indices.items():
        for word_index in word_indices:
            word = index_to_word[word_index]
            token_id__token__document_id_results.append((word_index, word, docid))
    if do_print:
        print('token_id__token__document_id_results:', token_id__token__document_id_results)

    # Make a table of tokens where the tuple is (doc_id, TFIDF ratio).
    doc_id__TFIDF_ratio_results = list()
    for documentid, word__idorstr__to_count__this_doc in documentid_to_word__idorstr__to_count.documentid_to_word__idorstr__to_count.items():
        for word__idorstr, this_word_count_this_document in word__idorstr__to_count__this_doc.items():
            if isinstance(word__idorstr, int):
                word = index_to_word[word__idorstr]
            else:
                word = word__idorstr
            word_index = word_to_index[word]

            total_word_count_this_document = documentid_to_word__idorstr__to_count.docid_to_wordcount_this_doc[docid]

            # total number of documents the word appears in
            num_docs_with_this_word = word_index_to_doc_count_per_word[word_index]

            tf = this_word_count_this_document / total_word_count_this_document
            idf = math.log(
                total_number_of_documents / num_docs_with_this_word,
                2
            )
            tfidf = tf * idf
            doc_id__TFIDF_ratio_results.append((documentid, word, tfidf))

    if do_print:
        # List comprehension to generate a tuple for each word (word, df, tfidf)
        results = [
            (
                index_to_word[word_index],
                number_of_docs_this_word_appears_in,
                math.log(total_number_of_documents/number_of_docs_this_word_appears_in, 2),
            ) 
            for word_index, number_of_docs_this_word_appears_in in word_index_to_doc_count_per_word.most_common()
        ]
        print("Results: ")
        print('doc_id__TFIDF_ratio_results (doc_id__TFIDF_ratio_results):', doc_id__TFIDF_ratio_results)
        print('total_number_of_documents (total_number_of_documents):', total_number_of_documents)
        print('total_word_count_all_documents (total_word_count_all_documents):', total_word_count_all_documents)
        print('average number of words per document (total_word_count_all_documents / total_number_of_documents): {:.2f}'.format(total_word_count_all_documents / total_number_of_documents))
        print('Token Data: ')
        print("Format: (word, unqiue document occurences, tf-idf)")
        for result in results:
            print(result)

    return doc_id__TFIDF_ratio_results


content_generators = [
    (
        "Generate tokens from any local document or directory of documents",
        lambda files_or_dirs: get_file_or_dir_contents(files_or_dirs=files_or_dirs),
    )
]

def run_main():
    args = parse_cl_args()

    do_print = not args.dont_print
    print_progress_int = {
        None: 100,
        False: -1,
    }.get(args.print_progress, args.print_progress)

    content_generator = get_file_or_dir_contents(args.file_or_dir)
    run_tokenize(
        args.file_or_dir,
        process_count=args.num_workers,
        do_print=do_print,
        content_generator=content_generator,
        print_progress_int=print_progress_int,
    )

    success = True
    return success

def parse_cl_args():
    argParser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    argParser._action_groups.pop()

    required = argParser.add_argument_group('Required arguments')
    required.add_argument(
        'file_or_dir', nargs='*',
        help="A text file or a directory containing text files\n"
            "that are to be read and tokenized. Note that this\n"
            "is not recursive - all documents should be at the base level\n"
            "of the directory."
    )

    options = argParser.add_argument_group('Options')
    options.add_argument('--num-workers', default=8, type=int)
    options.add_argument('--dont-print', default=False, action='store_true')

    options.add_argument(
        '--print-progress', default=False, type=int, nargs='?',
        help='Print the progress at given file interval. If specified without a parameter, print at every\n'
             '100 files.'
    )

    args = argParser.parse_args()
    return args

if __name__ == '__main__':
    success = run_main()
    exit_code = 0 if success else 1
    exit(exit_code)

