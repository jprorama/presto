# Presto - generate non-uniform data distributions

Project to create a data distribution profile for data sets
with the goal of interpolating post-compression non-uniform
data distributions to model large scale data sets.

## Running the code

Generating a non-uniform data distribution based on a given dataset involves a pipeline of 
three utilies:
* `data_dist.py`: generate a non-uniform data distribtion by compressing a dataset
* `filter_proc_size`: parse json ouput of specific compressor to extract process id and size
* `grid_interp.py`: create an interpolation of the input process list and size scaled in each dimension

The following example use the [hurricane Isabelle cloud dataset](https://www.earthsystemgrid.org/dataset/isabeldata/file.html).  Download a copy of one of the models generated by WRF, in this case hour 48, 
and uncompress the downloaded data:
```
wget https://www.earthsystemgrid.org/api/v1/dataset/isabeldata/file/CLOUDf48.bin.gz
gunzip CLOUDf48.bin.gz
```

The pipeline creates a non-unform distribution of data over eight processes (2x2x2) using sz 
compression, filters the procid and size values, and then doubles each process
dimension (2x2x2) using tri-linear interpolation over the given date. This will generate an 
interpolated data distribution across 64 process (an 4x4x4 process grid).

```
./runcmd data_dist.py  CLOUDf48.bin --shape 100x500x500 --reshape 50x250x250 -c sz -j | \
./filter_proc_size | \
./grid_interp.py -d 2x2x2 -s 2x2x2
```


The `data_dist.py` script 
takes the `CLOUDf48.bin` file as input, defines its given shape as 100x500x500 and then splits it into
8 parts of 50x250x250 each.  Each part is compressed using sz and JSON output is produced that includes
many metrics related to the compression. The `data_dist.py` script is run via a wrapper that invokes
the code in the context of the libpressio container.

The `filter_proc_size` script parses the JSON and extracts the process ID and compressed data set size.
It prints the result of each `procid size`, one per line. In this case, that produces 8 lines for a 
2x2x2 process grid.

The `grid_interp.py` takes the non-uniform distribution over 8 processes `-d 2x2x2` and produces a 2x
scaling in each dimension `-s 2x2x2`.  The resulting output generates a data distribution across
64 processes each on a separate line formatted as `procid size`.

Note: the `data_dist.py` non-uniform generator works in the dimensions of the input dataset using 
(slice x row x col). The `grid_interp.py` interpolation utility works in the dimensions of the process
grid using familar X,Y,Z row-major indexing.

## Limitations

* The utilities expect 3D so all inputs should specify values for each dimension.
* The project depends on the containerized [libpressio compresson library](https://github.com/CODARcode/libpressio) which must be installed to run `data_dist.py`.
