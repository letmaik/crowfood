from __future__ import absolute_import, print_function

import os
from collections import defaultdict

import crowfood.cli as cli
import crowfood.engine as engine

def test():
    deps = run('project-a')
    check_deps({'liba/a.c': {'liba/a.h'},
                'libb/b.c': {'libb/b.h'},
                'libb/b.h': {'liba/a.h'}}, deps)

def testSearchPath():
    deps = run('project-a/libb', ['-I', abspath('project-a')])
    check_deps({'b.h': {'liba/a.h'},
                'b.c': {'b.h'}}, deps)
    
def testMerge():
    deps = run('project-a', ['--merge', 'module'])
    check_deps({'libb/b': {'liba/a'}}, deps)

def abspath(path):
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, path)

def run(testpaths, argv=[]):
    if not isinstance(testpaths, list):
        testpaths = [testpaths]
    
    paths = list(map(abspath, testpaths))
    args = cli.parseargs(argv + paths)
    return engine.run(args)

def check_deps(expected, actual):
    act = defaultdict(set)
    for ((_,p1),(_,p2)) in actual:
        if p2 is None:
            continue
        act[p1.replace(os.sep, '/')].add(p2.replace(os.sep, '/'))
        
    assert expected == act, 'dependencies mismatch: \nactual:\n{}\n\nexpected:\n{}'.format(dict(act),expected)
    
if __name__ == '__main__':
    test()
    testSearchPath()
    testMerge()
    
    