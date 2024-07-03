#!/usr/bin/env python

from pathlib import Path
from pprint import pprint
import json
import numpy as np
import itertools
import sys
import argparse
import math

# procs to model
parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description='''
                                 Generate artificial distribution based on ranks (process count)
                                 memory per rank, and number of writers.
                                 Writers are defined by skip parameter which skips every dan process
                                 Eg. can be used to gather the compression size per process
                                 ''')
parser.add_argument("-d", "--debug", default=False,
                    help="print debug data to stderr")
parser.add_argument("-p", "--processes", default="8",
                    help="process count")
parser.add_argument("-m", "--memshape", default="100x500x500",
                    help="memory dimensions dataset is loaded into")
parser.add_argument("-s", "--skip", default="1",
                    help="number of ranks to skip data")
parser.add_argument("-t", "--dtype", default="float32",
                    help="dataset type")
parser.add_argument("-j", "--json", action='store_true',
                    help="enable json output, otherwise pprint python")
args = parser.parse_args()

debug=args.debug
processes = args.processes
jsonout=args.json
mem_shape=[int(x) for x in args.memshape.split("x")]
skip = int(args.skip)

if (args.dtype == "float64"):
    datatype=np.float64
elif (args.dtype == "int32"):
    datatype=np.int32
elif (args.dtype == "byte"):
    datatype=np.byte
else:
    datatype=np.float32

#
# use main idiom
#
if __name__ == '__main__':

    ranks = int(processes)

    #input_size = math.prod(dataset_shape)
    mem_size = 1
    for i in range(len(mem_shape)):
        mem_size = mem_size * int(mem_shape[i]) # math.prod(mem_shape)
    mem_bytes = mem_size * np.dtype(datatype).itemsize

    mpr = mem_bytes
    
    nulldata = 0
    for i in range(ranks):
        if (not i % skip): print(f"{i} {mpr}")
        else: print(f"{i} {nulldata}")
