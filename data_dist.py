#!/usr/bin/env python

from pathlib import Path
from pprint import pprint
import json
import libpressio
import numpy as np
import itertools
from mpi4py.futures import MPICommExecutor
import sys
import argparse

# procs to model
parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description='''
                                 Run libpressio compression on dataset using the given
                                 process count split and return statistics on compression
                                 across processes.
                                 Eg. can be used to gather the compression size per process
                                 ''')
parser.add_argument("-n", "--nprocs", default=1, type=int,
                    help="number of processes to split dataset across")
parser.add_argument("dataset",
                    help="dataset to compress")
parser.add_argument("-s", "--shape", default="100x500x500",
                    help="dataset dimensions")
parser.add_argument("-r", "--reshape", default="25x250x250",
                    help="new dataset dimensions, must divide dataset dimensions evenly")
parser.add_argument("-b", "--bounds", default="-6",
                    help="commas separated list of compression bounds, 10**n")
parser.add_argument("-c", "--compressors", default="sz,zfp",
                    help="comma separated list of compressors to select")
parser.add_argument("-t", "--dtype", default="float32",
                    help="dataset type")
parser.add_argument("-j", "--json", action='store_true',
                    help="enable json output, otherwise pprint python")
args = parser.parse_args()

procs=args.nprocs # derived from new shape
dataset=args.dataset
jsonout=args.json
dataset_shape=[int(x) for x in args.shape.split("x")]
dataset_newshape=[int(x) for x in args.reshape.split("x")]
bounds=[10**int(x) for x in args.bounds.split(",")]
compressors=[x for x in args.compressors.split(",")]

if (args.dtype == "float64"):
    datatype=np.float64
elif (args.dtype == "int32"):
    datatype=np.int32
else:
    datatype=np.float32

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

def cubify(arr, newshape):
    '''
    Reshape 3D shape into new 3D shape
    
    Credit: https://stackoverflow.com/a/42298440
    Tutorial for reshaping: https://realpython.com/numpy-reshape/
    '''
    oldshape = np.array(arr.shape)
    repeats = (oldshape / newshape).astype(int)
    tmpshape = np.column_stack([repeats, newshape]).ravel()
    order = np.arange(len(tmpshape))
    order = np.concatenate([order[::2], order[1::2]])
    # newshape must divide oldshape evenly or else ValueError will be raised
    return arr.reshape(tmpshape).transpose(order).reshape(-1, *newshape)

def run_compressor(args):
    compressor = libpressio.PressioCompressor.from_config({
        # configure which compressor to use
        "compressor_id": args['compressor_id'],
        # configure the set of metrics to be gathered
        "early_config": {
            "pressio:metric": "composite",
            "composite:plugins": ["time", "size", "error_stat"], 
        },
        # configure the compressor
        "compressor_config": args['compressor_config']
        })

    # run compressor to determine metrics
    idx=args['idx']
    decomp_data = args["data"][idx].copy()
    comp_data = compressor.encode(args["data"][idx])
    decomp_data = compressor.decode(comp_data, decomp_data)
    metrics = compressor.get_metrics()

    return {
        "compressor_id": args['compressor_id'],
        "bound": args['bound'],
        "proc_id" : args['idx'],
        "shape": "x".join(str(x) for x in np.shape(input_data[idx])),
        "metrics": metrics
    }

# load dataset, create output path
input_path = Path(__file__).parent / dataset
input_data = np.fromfile(input_path, dtype=datatype).reshape(dataset_shape)

input_data = cubify(input_data, dataset_newshape)

configs = [{
        "compressor_id": compressor_id,
        "compressor_config": {
            "pressio:abs": bound
        },
        "bound": bound,
        "idx": idx,
        "data": input_data
    } for bound, idx, compressor_id in
        itertools.product(
            np.array(bounds),
            range(input_data.shape[0]),
            compressors
        )
    ]



buff = dict();
index = 0
with MPICommExecutor() as pool:
    for result in pool.map(run_compressor, configs, unordered=True):
        algo = configs[index]['compressor_id']
        if algo in buff:
            buff[algo].append(result)
        else:
            buff[algo] = list()
            buff[algo].append(result)
        index+=1

if (jsonout):
    print(json.dumps(buff, indent=1, cls=NpEncoder))
else:
    pprint(buff)
