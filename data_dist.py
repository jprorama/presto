#!/usr/bin/env python

from pathlib import Path
from pprint import pprint
import json
import libpressio
import numpy as np
import itertools
from mpi4py.futures import MPICommExecutor
import sys

# procs to model
procs=int(sys.argv[1])

# load dataset, create output path
input_path = Path(__file__).parent / "datasets/CLOUDf48.bin.f32"
input_data = np.fromfile(input_path, dtype=np.float32).reshape(100, 500, 500)

input_data = np.array_split(input_data, procs, axis=0)

configs = [{
        "compressor_id": compressor_id,
        "compressor_config": {
            "pressio:abs": bound
        },
        "bound": bound,
        "idx": idx
    } for bound, idx, compressor_id in
        itertools.product(
            np.logspace(-6, -5, num=1),
            range(procs),
            ["sz", "zfp"]
        )
    ]


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
    decomp_data = input_data[idx].copy()
    comp_data = compressor.encode(input_data[idx])
    decomp_data = compressor.decode(comp_data, decomp_data)
    metrics = compressor.get_metrics()

    return {
        "compressor_id": args['compressor_id'],
        "bound": args['bound'],
        "shape": "x".join(str(x) for x in np.shape(input_data[idx])),
        "metrics": metrics
    }

with MPICommExecutor() as pool:
    for result in pool.map(run_compressor, configs, unordered=True):
        pprint(result)
