from __future__ import absolute_import, print_function

import sys
import os
import argparse
from warnings import warn

import crowfood.engine
from crowfood.utils import is_subdir

description = '''
See sfood for output format.
'''

def getParser():
    parser = argparse.ArgumentParser(prog='cfood', 
                                     description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', help='file or directory to scan (directory becomes a hierarchy root)', 
                        nargs='+',
                        )
    
    parser.add_argument('--quotetypes', help=
                        'Select for parsing the files included by strip quotes or angle brackets:\n'
                        'both - the default, parse all headers\n'
                        'angle - include only "system" headers included by anglebrackets (<>)\n'
                        'quote - include only "user" headers included by strip quotes ("")',
                        default='both', choices=['both', 'angle', 'quote'])
    
    parser.add_argument('--ext', help='an additional extension for files to be scanned\n'
                                      'default: c, h, cc, cpp, cxx, hpp, hxx',
                        action='append', default=[], dest='additional_exts',
                        )
    
    parser.add_argument('--merge', help='file - the default, treats each file as separate\n'
                                        'module - merges .c/.cc/.cpp/.cxx and .h/.hpp/.hxx pairs',
                        default='file', choices=['file', 'module'])
    
    parser.add_argument('-i','--ignore', help='directory to ignore', 
                        dest='ignore_paths', metavar='IGNORE',
                        action='append', default=[],
                        )
    
    parser.add_argument('-I','--include', help=
                        'additional include search path (for external dependencies\n'
                        'or when directory to scan does not correspond to #include path)',
                        dest='include_paths', metavar='INCLUDE',
                        action='append', default=[],
                        )
    
    parser.add_argument('--no-include-current', help=
                        'Do not search for includes in the folder of the '
                        'currently scanned file',
                        dest='no_include_current',
                        action='store_true',
                        )
    
    parser.add_argument('--fuzzy', help=
                        'Try to locate all non-found includes by matching '
                        'with file name only. Note that this may lead to '
                        'wrong dependencies.',
                        dest='fuzzy',
                        action='store_true',
                        )
    
    parser.add_argument('-E','--external-root', help=
                        'root directory to use for additional -I include paths for external dependencies'
                        'if not given, then the -I directories become the roots instead',
                        dest='external_roots', metavar='ROOT',
                        action='append', default=[],
                        )
    
    parser.add_argument('--print-roots', help='Only print the roots, useful for testing', 
                        dest='print_roots',
                        action='store_true',
                        )
    
    return parser

def parseargs(argv):
    parser = getParser()
    if not argv:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args(argv)
    
    for path in args.include_paths:
        if not os.path.isdir(path):
            parser.error('{} is not a directory'.format(path))
            
    for path in args.ignore_paths:
        if not os.path.isdir(path):
            warn.warn('{} is not a directory'.format(path))
            
    for path in args.path:
        if not os.path.exists(path):
            parser.error('{} does not exist'.format(path))
            
    for ext_root in args.external_roots:
        if not os.path.isdir(ext_root):
            parser.error('{} is not a directory'.format(ext_root))
        if not any(is_subdir(include_path, ext_root) for include_path in args.include_paths):
            parser.error('The external root {} must have at least ' +
                         'one matching -I subdirectory'.format(ext_root))

    args.include_paths = list(map(os.path.abspath, args.include_paths))
    args.external_roots = list(map(os.path.abspath, args.external_roots))
    args.ignore_paths = list(map(os.path.abspath, args.ignore_paths))    
    args.path = list(map(os.path.abspath, args.path))
    
    return args

def main():
    args = parseargs(sys.argv[1:])
    
    if args.print_roots:
        input_roots, input_include_paths, external_roots, external_include_paths =\
            crowfood.engine.get_roots_and_include_paths(args)
        print('input roots:')
        print(input_roots)
        print('input roots search paths:')
        print(list(input_include_paths.values()))
        print('external roots:')
        print(external_roots)
        print('external roots search paths:')
        print(list(external_include_paths.values()))
        sys.exit()
    
    for dep in sorted(crowfood.engine.run(args)):
        print(dep)
    
    
if __name__ == '__main__':
    main()
    