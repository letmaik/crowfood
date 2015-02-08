from __future__ import print_function, absolute_import

from six.moves import filter
from io import open # to use encoding kw in Python 2

import os
from collections import defaultdict

from crowfood.utils import is_subdir
import re
import sys
import itertools

def get_roots_and_include_paths(args):
    # convention:
    # input roots are the directories of the files to scan
    # include roots are the directories given by -I
    input_roots = set()
    for path in args.path:
        if os.path.isfile(path):
            path = os.path.dirname(path)
        input_roots.add(path)
        
    external_roots = set(args.external_roots)
    # make any include path an additional external root if it is outside any existing root 
    external_roots.update(
        set(filter(lambda include_path: not any(is_subdir(include_path, root) 
                                                for root in input_roots.union(external_roots)), 
                   args.include_paths)))
    
    input_include_paths = defaultdict(list) # input root -> include paths
    external_include_paths = defaultdict(list) # external root -> include paths
    for include_path in args.include_paths:
        input_root = [root for root in input_roots if is_subdir(include_path, root)]
        if input_root:
            input_include_paths[input_root[0]].append(include_path)
        else:
            external_root = [root for root in external_roots 
                             if is_subdir(include_path, root) or include_path == root]
            external_include_paths[external_root[0]].append(include_path)
    
    for root in input_roots:
        if root not in input_include_paths: 
            input_include_paths[root].append(root)        
    for root in external_roots:
        if root not in external_include_paths: 
            external_include_paths[root].append(root)
    
    return input_roots, input_include_paths, external_roots, external_include_paths

def run(args):
    input_roots, input_include_paths, external_roots, external_include_paths =\
        get_roots_and_include_paths(args)
        
    # for every found directory and file we need to output:
    #((root, 'relative/path/to/root'), (None, None))
        
    # We scan all requested files and directories and stop at the outer
    # level of any dependencies found at the include search paths.
    # Files in the include paths are not scanned for #include's.
    
    # Get a list of all files with .c/.cc/.cpp/.cxx/.h/.hpp/.hxx extension
    # from the directories to scan for, if any.
    exts = ['c', 'h', 'cc', 'cpp', 'cxx', 'hpp', 'hxx'] + args.additional_exts
    files = defaultdict(list) # input root -> file paths relative to root

    def get_input_root(path):
        return next(filter(lambda root: root in path, input_roots))
    
    for path in args.path:
        if os.path.isfile(path):
            root = get_input_root(path)
            files[root].append(os.path.relpath(path, root))
        else:
            for base, _, filenames in os.walk(path):
                if base in args.ignore_paths:
                    continue
                root = get_input_root(base)
                filenames = filter(lambda f: any(f.endswith('.' + ext) for ext in exts), filenames)
                filepaths = map(lambda f: os.path.join(base, f), filenames)
                filepaths = map(lambda p: os.path.relpath(p, root), filepaths)
                files[root].extend(filepaths)
                
    # parse the #include's of all files
    quotes = dict({'both': ('["|<]', '["|>]'),
                   'angle': ('<', '>'),
                   'quote': ('"', '"')
                   })[args.quotetypes]
    include_re = re.compile(r'#include {}([a-zA-Z0-9_\-\.\/]+){}'.format(*quotes))
    includes = dict() # (root,relpath) -> [include paths]
    for root, filepaths in files.items():
        for filepath in filepaths:
            print('parsing', filepath, file=sys.stderr)
            with open(os.path.join(root, filepath), encoding='utf8') as fp:
                includes[(root,filepath)] = include_re.findall(fp.read())
            
    # for each include, find the root it belongs to
    includes_roots = dict() # include path -> root
    includes_unique = set(itertools.chain.from_iterable(includes.values()))
    
    def find_in_root(include, root, include_paths, cache=None):
        for include_path in include_paths:
            full_path = os.path.join(include_path, include)
            rel = os.path.relpath(full_path, root)
            if cache:
                if rel in cache[root]:
                    return rel
            elif os.path.exists(full_path):
                return rel
        return False
    
    def find_in_roots(include, root_includepaths, cache=False):
        for root, include_paths in root_includepaths:
            rel = find_in_root(include, root, include_paths, cache)
            if rel:
                return root, rel
        return False, False
    
    for include in includes_unique:
        # first we search within the input roots, then in the external roots                
        root, relpath = find_in_roots(include, input_include_paths.items(), files)
        if not root:
            root, relpath = find_in_roots(include, external_include_paths.items())
        if root:
            includes_roots[include] = root, relpath
    
    not_found = []
    for (root, filepath), includepaths in list(includes.items()):
        includes[(root, filepath)] = []
        for include in includepaths:
            root_path = False
            if not args.no_include_current:
                # look in current folder and prefer this over the other results
                rel = find_in_root(include, root, 
                                   [os.path.join(root, os.path.dirname(filepath))], files)
                if rel:
                    root_path = root, rel
            if not root_path:
                root_path = includes_roots.get(include)
            if root_path:
                includes[(root, filepath)].append((root_path[0],root_path[1]))
            else:
                not_found.append((include, filepath))
                
    if not_found:
        print('\nWARNING: some includes could not be found:\n', file=sys.stderr)
        for include,filepath in not_found:
            print('{} not found (from {})'.format(include, filepath), file=sys.stderr)
    
    # Unify roots when a file was found over multiple roots.
    # This happens when an include search path is given that is above
    # an internal root.
    roots = input_roots.union(external_roots)
    nested_roots = list(filter(lambda r: is_subdir(*r), itertools.product(roots, roots)))
    if nested_roots:
        print('going to unify paths as there are nested roots', file=sys.stderr)
        
        def move_root(subroot, root, filepath):
            full = os.path.join(root, filepath)
            if is_subdir(full, subroot) or os.path.dirname(full) == subroot:
                rel = os.path.relpath(full, subroot)
                print('moving root: {} -> {} for {}'.format(root, subroot, filepath), file=sys.stderr)
                return (subroot, rel)
            else:
                return (root, filepath)
                
        for subroot,root in nested_roots:
            # the strategy is to move all includes from root to the subroot if they
            # are actually within the subroot
            for rf,includepaths in includes.items():
                includes[rf] = [move_root(subroot,root,filepath) if root_ == root else (root_,filepath)
                                for root_,filepath in includepaths]
    
    # merge .h/.c files if requested
    if args.merge == 'module':
        # The tricky part is: how do we know which files belong together?
        # Obviously this is only possible if there is a 1-1 relationship
        # in naming of the .c/.h files, that is the base is the same.
        # Also, the .h file must be included in the matching .c file.
        # We merge transitive dependencies of the same base name
        # into the including .c file entry, thereby collapsing
        # the dependencies of the matching files.
        
        def find_matches(base, includepaths):
            ''' returns a list of (root,filepath) items '''
            if not includepaths:
                return []
            matches = ((root,filepath) for (root,filepath) in includepaths
                       if os.path.splitext(os.path.basename(filepath))[0] == base)
            return itertools.chain(matches, 
                                   itertools.chain.from_iterable(
                                        find_matches(base, includes[match])
                                        for match in matches)
                                   )
        
        for (root,filepath),includepaths in list(includes.items()):
            if (root,filepath) not in includes:
                # already merged
                continue
            filename = os.path.basename(filepath)
            base,ext = os.path.splitext(filename)
            if not ext.startswith('.c'):
                continue
            
            # Recursively get all includes with matching base name
            # starting from the current c file.
            # This becomes the set of files to merge into the including .c entry.
            # Recursion only follows paths where the base name matches,
            # that is, a.c -> a.h -> a.inc will be picked up, but not
            # a.c -> b.h -> a.inc.
            # Cyclic imports will lead to an error.
            matches = set(find_matches(base, includepaths))
            
            deps = itertools.chain.from_iterable(includes.get(match, []) for match in matches)
            includes[(root,filepath)] = list((set(includepaths) | set(deps)) - matches)
            
            for match in matches:
                if match in includes:
                    del includes[match]
        
        # remove file extensions as these don't make sense anymore now
        newincludes = dict()
        for (root1,path1),includepaths in includes.items():
            newincludes[(root1,os.path.splitext(path1)[0])] =\
                [(root2,os.path.splitext(path2)[0]) for (root2,path2) in includepaths]
        includes = newincludes
            
    # maybe: replace file extension with .py to make snakefood happy
    
    
    
    # return dependencies as ((root,path),(root,path)) tuples
    deps = []
    dirs = {}
    for (root,filepath),includepaths in includes.items():
        deps.append(((root,filepath),(None,None)))
        
        directory = os.path.dirname(os.path.join(root, filepath))
        if directory not in dirs:
            deps.append(((root,os.path.dirname(filepath)),(None,None)))
        
        for root_,filepath_ in includepaths:
            deps.append(((root,filepath),(root_,filepath_)))
            
            directory = os.path.dirname(os.path.join(root_, filepath_))
            if directory not in dirs:
                deps.append(((root_,os.path.dirname(filepath_)),(None,None)))
    return deps            
    