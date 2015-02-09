"""
Cluster dependencies by regular expression.
"""
# This file is part of the Snakefood open source package.
# See http://furius.ca/snakefood/ for licensing details.

import sys
import re
from itertools import imap

from snakefood.fallback.collections import defaultdict
from snakefood.depends import read_depends, output_depends


def iterpairs(thelist):
    ilist = iter(thelist)
    while 1:
        yield next(ilist), next(ilist)

def read_clusters(fn):
    "Return a list of cluster regexes read from the file 'fn'."
    f = open(fn, 'rU')
    clusters = []
    for x in imap(str.strip, f.xreadlines()):
        if not x:
            continue
        regex, rename = x.split(' ')
        clusters.append(regex)
        clusters.append(rename)
    return clusters

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    
    parser.add_option('-f', '--from-file', action='store',
                      help="Read cluster list from the given filename.")
    
    opts, renames = parser.parse_args()

    if opts.from_file:
        renames.extend(read_clusters(opts.from_file))

    if len(renames) % 2:
        parser.error("An odd number of renames was specified.")

    renames = [(re.compile(regexp), target)
               for regexp, target in iterpairs(renames)]

    depends = read_depends(sys.stdin)

    clusfiles = defaultdict(set)
    for (froot, f), (troot, t) in depends:
        for rename, target in renames:
            if rename.match(f):
                f = target
                break
        cfrom = (froot, f)
        for rename, target in renames:
            if t and rename.match(t):
                t = target
                break
        cto = (troot, t)

        # Skip self-dependencies that may occur.
        if cfrom == cto:
            cto = (None, None)

        clusfiles[cfrom].add(cto)

    output_depends(clusfiles)
