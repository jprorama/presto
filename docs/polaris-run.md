# Getting started with NUIO and h5bench on polaris

## start a debug job
```
qsub -I -l select=1:ncpus=64 -l filesystems=home:eagle -l walltime=1:00:00 -q debug -A dist_relational_alg
```

## set proxies for job Internet access
```
# SET proxy for internet access to data

export HTTP_PROXY=http://proxy.alcf.anl.gov:3128
export HTTPS_PROXY=http://proxy.alcf.anl.gov:3128
export http_proxy=http://proxy.alcf.anl.gov:3128
export https_proxy=http://proxy.alcf.anl.gov:3128

```

## One-time setup

### clone the presto workflow project

```
git clone https://github.com/jprorama/presto.git
cd presto
```

### make yourself a data location on lustre

for the write tests and outputs and data sets

```
export DATA_DIR=/eagle/dist_relational_alg/$USER/presto-data
mkdir -p $DATA_DIR/data
mkdir -p $DATA_DIR/storage
mkdir -p $DATA_DIR/datasets

```

### link to the data dirs from your presto project

```
ln -s $DATA_DIR/data
ln -s $DATA_DIR/storage
ln -s $DATA_DIR/datasets

```

### download hurricane ISABEL data set

```
mkdir -p datasets/ISABEL
pushd datasets/ISABEL
wget https://g-8d6b0.fd635.8443.data.globus.org/ds131.2/Data-Reduction-Repo/raw-data/Hurricane-ISABEL/SDRBENCH-Hurricane-ISABEL-100x500x500.tar.gz
tar -xzf SDRBENCH-Hurricane-ISABEL-100x500x500.tar.gz
popd

```

## Per-job setup

In addition to the proxies above, if you plan to download data sets

### setup env for user

This sets up access to the libpressio utilites, custom h5bench, 
and other utilities used by project.

```
export NUIO_INSTALL_DIR=/eagle/dist_relational_alg/nuio


# activate spack
. $NUIO_INSTALL_DIR/spack/share/spack/setup-env.sh

## load spack modules
spack load libpressio
spack load py-scipy

# load h5bench with hdf5+subfiling+async
PATH=$NUIO_INSTALL_DIR/bin/:$PATH
LD_LIBRARY_PATH=$NUIO_INSTALL_DIR/lib:$LD_LIBRARY_PATH

```

## Generate non-uniform data set

test generation of non-uniform data set for 8 processes from cloudf48.bin ISABEL data set
```
mpiexec -n 8 ./data_dist.py -s 100x500x500 -r 50x250x250 -c sz3 -j datasets/ISABEL/100x500x500/CLOUDf48.bin.f32  | ./filter_proc_size sz3 > cloud-8
```

scale the data set to 64 process 2x in each dimension from 2x2x2 to 4x4x4 using interpolation
```
cat cloud-8 | ./grid_interp.py -d 2x2x2 -s 2x2x2 > cloud-64

```

## Run h5bench benchmarks

Run h5bench for standard sync and async writes and newly generated non-uniform 64 rank data distribution in cloud-64.
The results dir in `storate/` will be listed and the stdout file contains performance stats.

sync with uniform distribution
```
h5bench --debug examples/sync-write-1d-contig-contig.json

```

sync+subfiling with uniform distribution.
Adjust the per-node and thread-pool to explore different subfiling configurations.
```
H5FD_SUBFILING_IOC_PER_NODE=1 H5FD_IOC_THREAD_POOL_SIZE=2 h5bench --debug examples/sync-write-1d-contig-contig-subfiling.json

```

sync with data distribtion of cloud-64
```
h5bench --debug examples/sync-write-1d-contig-contig-data-dist.json
  
```

async with uniform distribution
```
h5bench --debug examples/async-write-1d-contig-contig.json

```
