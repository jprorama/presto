#!/usr/bin/env python

from pathlib import Path
from pprint import pprint
import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import sys
import argparse
import fileinput

# procs to model
parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description='''
                                 Run SciPy RegularGridInterpolator on input dataset using the given
                                 process dimensions and producing an interpolated result for the
                                 output process dimensions. Defaults to no interpolation so
                                 input should equal output.
                                 ''')
parser.add_argument("-n", "--nprocs", default=1, type=int,
                    help="number of processes to split dataset across")
parser.add_argument("files", nargs="*",
                    help="dataset to interpolate, stdin by default")
parser.add_argument("-d", "--dimensions", default="4x2x2",
                    help="dataset input dimensions, (slice, row, col) row-major")
parser.add_argument("-s", "--scale", default="1x1x1",
                    help="new interpolated dimensions scaling factor per dimension")
parser.add_argument("-t", "--dtype", default="float32",
                    help="dataset type")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="produce verbose output of all data structures for debug")
args = parser.parse_args()

procs=args.nprocs # derived from new shape
shape=[int(x) for x in args.dimensions.split("x")]
scale=[int(x) for x in args.scale.split("x")]

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


# load dataset, create output path
#input_path = Path(__file__).parent / dataset
#input_data = np.fromfile(input_path, dtype=datatype).reshape(dataset_shape)

gridvalues = list()

# https://www.digitalocean.com/community/tutorials/read-stdin-python
# https://gist.github.com/martinth/ed991fb8cdcac3dfadf7
for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', ), encoding="ascii"):
    _, x = line.split() # ignore index and treat as row major
    gridvalues.append(x)

# cast to datatype https://stackoverflow.com/a/3877247/8928529
gridvalues = np.array(gridvalues).astype(datatype)

# build regular grid model for interpolator
# index values of x,y,z
x=np.arange(shape[1])
y=np.arange(shape[2])
z=np.arange(shape[0])

c_space = RegularGridInterpolator((z, x, y), gridvalues.reshape(shape))

# compute scaled interpolation dimensions
newx=np.linspace(x[0],x[-1],len(x)*scale[1])
newy=np.linspace(y[0],y[-1],len(y)*scale[2])
newz=np.linspace(z[0],z[-1],len(z)*scale[0])

# generate data points for new interpolated grid
# note: seems like np.meshgrid() should work but can't produce correct point order

newgrid = np.zeros((len(newx)*len(newy)*len(newz),3))

i = 0
for zslice in newz:
    for row in newx:
        for col in newy:
            newgrid[i] = [zslice, row, col]
            i+=1

# generate interpolated grid points
gen_compress = c_space(newgrid).reshape(len(newz), len(newx), len(newy))

# dump raw values for debug
if (args.verbose):
    pprint([gridvalues.reshape(shape), shape, [z,x,y],
            gen_compress, gen_compress.shape, (len(newz), len(newx), len(newy)), [newz, newx, newy]])

# print scaled output proc_id and size, row-major global coordinate system
for i, value in enumerate(gen_compress.ravel()):
    print(f"{i} {value}")
