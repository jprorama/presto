#!/usr/bin/env python

from pathlib import Path
from pprint import pprint
import json
import libpressio
import numpy as np
import itertools
from mpi4py.futures import MPICommExecutor
from mpi4py import MPI
import sys
import argparse
import math

# procs to model
parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description='''
                                 Run libpressio compression on dataset using the given
                                 process count split and return statistics on compression
                                 across processes.
                                 Eg. can be used to gather the compression size per process
                                 ''')
parser.add_argument("dataset",
                    help="dataset to compress")
parser.add_argument("-d", "--debug", default=False,
                    help="print debug data to stderr")
parser.add_argument("-s", "--shape", default="100x500x500",
                    help="dataset dimensions")
parser.add_argument("-m", "--memshape", default="100x500x500",
                    help="memory dimensions dataset is loaded into")
parser.add_argument("-r", "--reshape", default="25x250x250",
                    help="new dataset dimensions, must divide memshape dimensions evenly")
parser.add_argument("-b", "--bounds", default="0.000001",
                    help="commas separated list of compression bounds as floats")
parser.add_argument("-c", "--compressors", default="sz,zfp",
                    help="comma separated list of compressors to select")
parser.add_argument("-t", "--dtype", default="float32",
                    help="dataset type")
parser.add_argument("-j", "--json", action='store_true',
                    help="enable json output, otherwise pprint python")
args = parser.parse_args()

debug=args.debug
dataset=args.dataset
jsonout=args.json
dataset_shape=[int(x) for x in args.shape.split("x")]
mem_shape=[int(x) for x in args.memshape.split("x")]
dataset_newshape=[int(x) for x in args.reshape.split("x")]
bounds=[float(x) for x in args.bounds.split(",")]
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

    idx=args['idx']

    # if we resize the last chunk, resize it
    if (args["resize"]):
        if debug: print(f"args['last_len']: {args['last_len']}", file=sys.stderr)
        if debug: print(f"input data shape: {args['data'].shape}", file=sys.stderr)
        cutoff  = args['last_len']
        trunc = args["data"].copy()
        trunc = trunc[:,:, :cutoff]
        args["data"] = trunc
        if debug: print(f"reshaped data: {args['data'].shape}", file=sys.stderr)

    # run compressor to determine metrics
    decomp_data = args["data"].copy()
    comp_data = compressor.encode(args["data"])
    decomp_data = compressor.decode(comp_data, decomp_data)
    metrics = compressor.get_metrics()

    return {
        "compressor_id": args['compressor_id'],
        "bound": args['bound'],
        "proc_id" : args['idx'],
        "shape": "x".join(str(x) for x in args["data"].shape),
        "metrics": metrics
    }

#
# use main idiom to protect the computations in the pool
#
# https://mpi4py.readthedocs.io/en/stable/mpi4py.futures.html#examples
#
if __name__ == '__main__':

    # load dataset, create output path
    input_path = Path(__file__).parent / dataset
    input_data = np.fromfile(input_path, dtype=datatype).reshape(dataset_shape)
    if debug: print(f"read shape: {input_data.shape}", file=sys.stderr)

    # if mem_size is bigger than input data copy into larger space
    # https://stackoverflow.com/a/7115957/8928529

    input_size = math.prod(dataset_shape)
    mem_size = math.prod(mem_shape)
    if (mem_size > input_size):
        # cast into larger memory footprint, assumes 3D
        mem_data = np.zeros(mem_shape, dtype=datatype)
        mem_data[0:input_data.shape[0], 0:input_data.shape[1], 0:input_data.shape[2]] = input_data
        input_data = mem_data
    if debug: print(f"mem shape: {input_data.shape}", file=sys.stderr)

    input_data = cubify(input_data, dataset_newshape)
    if debug: print(f"cubified shape: {input_data.shape}", file=sys.stderr)

    # test truncate last cube to original data size
    # only works for 1D data sets (i.e. resize of last dim only)
    # and only if we resized to artificial mem_size
    resize_last = False
    if (mem_size > input_size):
        if debug: print(f"input_data: {input_data.shape}", file=sys.stderr)
        if debug: print(f"input_data.shape[1]: {input_data.shape[1]}", file=sys.stderr)
        if debug: print(f"input_data.shape[2]: {input_data.shape[2]}", file=sys.stderr)
        if (input_data.shape[1]==1 and input_data.shape[2]==1):
            # take last cube and bring it back to size
            resize_last = True

    if debug: print(f"resize_last: {resize_last}", file=sys.stderr)

    idx_range = input_data.shape[0]
    last_len = 0 # assume we divide evenly
    if (resize_last):
        if debug: print(f"input_data.shape: {input_data.shape}", file=sys.stderr)
        if debug: print(f"dataset_shape: {dataset_shape}", file=sys.stderr)
        last_len = dataset_shape[2] % input_data.shape[3]
        if debug:print(f"idx_range: {idx_range} last_len: {last_len}", file=sys.stderr)

    # note: input_data[idx] are limited to < 2GiB of data
    # due to pickled message size limits in MPI-1/2/3
    # recommended to use pkl5 util to overcome limits
    # https://github.com/mpi4py/mpi4py/issues/119
    configs = [{
            "compressor_id": compressor_id,
            "compressor_config": {
                "pressio:abs": bound
            },
            "bound": bound,
            "idx": idx,
            "data": input_data[idx],
            "resize": (idx == (input_data.shape[0]-1) and resize_last),
            "last_len": last_len
        } for bound, idx, compressor_id in
            itertools.product(
                np.array(bounds),
                range(idx_range),
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

    rank = MPI.COMM_WORLD.Get_rank()
    if (rank == 0):
        if (jsonout):
            print(json.dumps(buff, indent=1, cls=NpEncoder))
        else:
            pprint(buff)
