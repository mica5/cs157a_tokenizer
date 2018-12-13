# cs157a_tokenizer

This project includes two different tools: 
-One tokenizer script that calculates TFiDF values on a
set of text documents, following the formula as defined 
by Dr. Ty Lin. 

-One 2 Concept script that finds all possible 2-concept
relations in a set of text documents.   

#Setup:
This project requires Python3+ to run. 
If you need python, releases can be found at:
https://www.python.org/downloads/release/

Windows requires the path to be updated. Run the install
as Admin. In the python install,there will be directions 
to update the path properly.It is offered as a checkbox 
in the advanced settings.
We assume zero responsibility for incorrect path setup.
A walk through on setting it up manually can be found here:
http://people.cs.ksu.edu/~schmidt/200f07/setpath.html

Once python is installed, the
additional library setup is as follows:
(Windows warning:these may need to be run in an Admin Console 
and called with pip3 insated of pip)

$ pip install numpy
$ pip install nltk
$ pip install beautifulsoup4 
$ pip install -U spacy
$ python -m spacy download en

#Running:
This section assumes you have installed all necessary dependencies
and are working in our project directory. 
You must also have ALL texts that you wish to group as one "cluster"
together in a directory.

Tokenizer:
$ parallel_tokenizer.py C:/Path/to/Text/Document/Directory

The whole path should be given. The output is printed to the console
and can be piped to the screen. 

Python 2-concept:
$ 2_Concepts_Project.py C:/Path/To/Directory/Of/Texts

For the Java project:
In the "Java 2 concept with tfidf" directory, run 
java TwoConceptReader.jar
The output can be piped to an file. 