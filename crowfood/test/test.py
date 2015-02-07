from __future__ import absolute_import, print_function

import os

import crowfood.cli as cli
import crowfood.engine as engine

def test():
    deps = run('project-a')
    check_deps({'liba/a.c': ['liba/a.h'],
                'libb/b.c': ['libb/b.h'],
                'libb/b.h': ['liba/a.h']}, deps)

def testSearchPath():
    deps = run('project-a/libb', ['-I', 'project-a'])
    check_deps({'b.h': ['liba/a.h'],
                'b.c': ['b.h']}, deps)
    
def testMerge():
    # FIXME merging is broken
    deps = run('project-a', ['--merge', 'module'])
    check_deps({'liba/a.c': [],
                'libb/b.c': ['liba/a.c']}, deps)
    
def run(testpaths, argv=[]):
    if not isinstance(testpaths, list):
        testpaths = [testpaths]
    here = os.path.abspath(os.path.dirname(__file__))
    paths = [os.path.join(here, testpath) for testpath in testpaths]
    args = cli.parseargs(argv + paths)
    return engine.run(args)

def check_deps(expected, actual):
    exp = {}
    for path, includes in expected.items():
        exp[path.replace('/', os.sep)] = [p.replace('/', os.sep) for p in includes]
    
    for path, includes in exp.items():
        for include in includes:
            assert any(path == p and include == p2 for ((_,p),(_,p2)) in actual),\
                '{} -> {} not existing in:\n{}'.format(path, include, pretty(actual))

def pretty(deps):
    lines = []
    for ((root1,path1),(root2,path2)) in deps:
        if not root2:
            continue
        lines.append('{} -> {}'.format(path1,path2))
    return '\n'.join(lines)

if __name__ == '__main__':
    test()
    testSearchPath()
    testMerge()
    
    