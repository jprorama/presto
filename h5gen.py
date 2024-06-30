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
                                 Generate h5bench json job script.
                                 ''')
parser.add_argument("configfile",
                    help="template h5bench json file")

# mpi parameters
parser.add_argument("-r", "--ranks", default="8",
                    help="rank count")
parser.add_argument("-p", "--procs", default="64",
                    help="processors per node")
parser.add_argument("--hostsfile",
                    help="hostsfile for mpi")
parser.add_argument("-t", "--threads", default="1",
                    help="dataset type")

# benchmark
parser.add_argument("-b", "--benchmark",
                    help="benchmark to run")

# output file controls
parser.add_argument("--hdf5file",
                    help="hdf5 output file for tests")
parser.add_argument("--mem_pattern", choices=["CONTIG","INTERLEAVED"], default="CONTIG",
                    help="storage pattern memory")
parser.add_argument("--file_pattern", choices=["CONTIG","INTERLEAVED"], default="CONTIG",
                    help="storage patterh file")

# timesteps and emulation timings
parser.add_argument("--timesteps",
                    help="timesteps to benchmark")
parser.add_argument("--cpt",
                    help="emulated compute time per timestep")
parser.add_argument("--dct",
                    help="delayed close timesteps")


# data set information
parser.add_argument("--dim1",
                    help="particles in dim 1")
parser.add_argument("--stdev_dim1",
                    help="particle standard deviation, for var_normal")
parser.add_argument("--datadist",
                    help="data distribution file")
parser.add_argument("--datascale",
                    help="data distribution scaling factor")

# other args
parser.add_argument("-j", "--json", action='store_true',
                    help="enable json output, otherwise pprint python")
args = parser.parse_args()

ranks = int(args.ranks)
ppn = int(args.procs)
threads = int(args.threads)
jsonout=args.json
benchmark = args.benchmark
hostsfile=args.hostsfile
datadist=args.datadist
datascale=args.datascale
configfile=args.configfile
hdf5file=args.hdf5file


# encoder for json to avoid int64 exceptons
#
# https://stackoverflow.com/a/57915246
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


#
# use main idiom
#
if __name__ == '__main__':

    with open(configfile) as json_data:
        h5b_cfg = json.load(json_data)
    
    h5b_cfg["mpi"]["configuration"] = f"-n {ranks} -ppn {ppn} --depth {threads} --hostsfile {hostsfile}"

    for i in range(len(h5b_cfg["benchmarks"])):
        if benchmark: h5b_cfg["benchmarks"][i]["benchmark"] = benchmark
        if hdf5file: h5b_cfg["benchmarks"][i]["file"] = hdf5file

        if args.timesteps: h5b_cfg["benchmarks"][i]["configuration"]["TIMESTEPS"] = args.timesteps
        if args.cpt: h5b_cfg["benchmarks"][i]["configuration"]["EMULATED_COMPUTE_TIME_PER_TIMESTEP"] = f"{args.cpt} s"
        if args.dct: h5b_cfg["benchmarks"][i]["configuration"]["DELAYED_CLOSE_TIMESTEPS"] = args.dct
        if datadist: h5b_cfg["benchmarks"][i]["configuration"]["DATA_DIST_PATH"] = datadist
        if datascale: h5b_cfg["benchmarks"][i]["configuration"]["DATA_DIST_SCALE"] = datascale
        if args.mem_pattern: h5b_cfg["benchmarks"][i]["configuration"]["MEM_PATTERN"] = args.mem_pattern 
        if args.file_pattern: h5b_cfg["benchmarks"][i]["configuration"]["FILE_PATTERN"] = args.file_pattern
        if args.dim1: h5b_cfg["benchmarks"][i]["configuration"]["DIM_1"] = args.dim1
        if args.stdev_dim1: h5b_cfg["benchmarks"][i]["configuration"]["STDEV_DIM_1"] = args.stdev_dim1
   
    print(json.dumps(h5b_cfg, indent=4, cls=NpEncoder))
