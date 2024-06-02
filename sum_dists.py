#!/usr/bin/env python

import sys
import argparse
import fileinput

# procs to model
parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description='''
                                 Run sum on multiple files with indexed numeric values, 1 per row
                                 ''')
parser.add_argument("files", nargs="*",
                    help="datasets to sum, stdin by default")
args = parser.parse_args()

sums = dict()

# https://www.digitalocean.com/community/tutorials/read-stdin-python
# https://gist.github.com/martinth/ed991fb8cdcac3dfadf7
for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', ), encoding="ascii"):
    idx, x = line.split() # ignore index and treat as row major
    idx, x = int(idx), int(x)
    if idx in sums:
        sums[idx] += x
    else:
        sums[idx] = x


# print scaled output proc_id and size, row-major global coordinate system
for i in sorted(sums):
    print(f"{i} {sums[i]}")
