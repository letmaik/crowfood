crowfood
========

.. image:: https://travis-ci.org/neothemachine/crowfood.svg?branch=master
    :target: https://travis-ci.org/neothemachine/crowfood

Creates dependency files from C/C++ code for use with 
`snakefood <https://bitbucket.org/blais/snakefood>`_.
This allows you to easily create dependency graphs on file/module/folder/etc. level from your C/C++ codebase.

Installation
------------

You must have Python installed on your system.

If you don't have snakefood installed yet, install it with ``pip install snakefood`` first.

Now install crowfood with ``pip install crowfood``.

How to create dependency graphs
-------------------------------
Getting started
'''''''''''''''

Let's assume `/libab` is the root path of your C/C++ project which contains:

.. code-block::

    A.c
    B.c
    ab/
        A.h
        B.h

We'll create a simple file-based dependency graph by piping crowfood's 
dependency information to snakefood's ``sfood-graph`` tool to create a graph in DOT format
which is then visualized with ``dot`` itself and saved to a pdf file:

.. code-block::

    cfood /libab | sfood-graph | dot -Tpdf > simple.pdf
    
crowfood can handle many folder layouts and will output warnings if it can't find #include's.
Run ``cfood --help`` to see all options regarding folder layout and include paths.

*TIP*: As a quick fix or to get started with bigger projects, 
use ``--fuzzy`` to let crowfood search for ``#include``ed files purely by their filename
and ignore folder structure.

Grouping/Clustering
'''''''''''''''''''

Depending on how big your project is it may make sense to group files together in some way.

One way is to group matching source and header files as "modules":

.. code-block::

    cfood /libab --merge module | sfood-graph | dot -Tpdf > modules.pdf

Another way is to define clusters in terms of path prefixes.
First, create a file ``clusters`` which contains the prefixes:

.. code-block::

    componenta
    componentb/partc
    
And then run:

.. code-block::

    cfood /bigproject | sfood-cluster -f clusters | sfood-graph | dot -Tpdf > clustered.pdf

Have a look at the `snakefood docs <http://furius.ca/snakefood/doc/snakefood-doc.html>`_
to get some more inspiration on how to transform the raw dependency output from crowfood
into something that makes sense for your project.
Always remember that the dependency output is line-based and very easy to handle with
standard unix tools, e.g. grep for filtering.
