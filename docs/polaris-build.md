# Notes for building h5bench test on polaris 

Clone hdf5, argobots, and vol-async into an hdf5-build dir.
Suggest placing these in a path like `~/projects/hdf5-build`.

Define your shared project space for the build artifacts.
```
export PROJECT_DIR=your_shared_project_dir
```
Can just copy-paste following once above are set up

Set up build environment:
```
export NUIO_INSTALL_DIR=$PROJECT_DIR/nuio
export H5_DIR=$HOME/projects/hdf5-build/hdf5
export VOL_DIR=$HOME/projects/hdf5-build/vol-async
export ABT_DIR=$HOME/projects/hdf5-build/vol-async/argobots
export H5B_DIR=$HOME/projects/h5b-cust
export HDF5_DIR=$NUIO_INSTALL_DIR
export HDF5_PLUGIN_PATH=$HDF5_DIR/lib
# fixes link errors during h5bench build
export LD_LIBRARY_PATH=$HDF5_DIR/lib:$LD_LIBRARY_PATH

module use /soft/modulefiles
module load spack-pe-base cmake

```

Build hdf5 with subfiling support:
```
cd $H5_DIR
rm -rf build
mkdir build
cd build

cmake -DCMAKE_INSTALL_PREFIX=$NUIO_INSTALL_DIR \
        -DHDF5_ENABLE_PARALLEL=ON \
        -DHDF5_BUILD_CPP_LIB:BOOL=OFF \
        -DHDF5_BUILD_JAVA:BOOL=OFF \
        -DHDF5_ENABLE_THREADSAFE=ON \
        -DHDF5_ENABLE_SUBFILING_VFD:BOOL=ON \
        -DALLOW_UNSUPPORTED=ON  ..

make -j && make install

```

Build argobots:
```
module load PrgEnv-gnu


cd $ABT_DIR
./autogen.sh
./configure --prefix=${NUIO_INSTALL_DIR}
make && make install


module load  PrgEnv-nvhpc/8.5.0

```

Build vol_async connector. 
Fixes `CMakeLists.txt` to reference custom includes and libraries
```
cd $VOL_DIR

patch -b CMakeLists.txt << EOF
8a9,12
> set (APT_INCLUDE_DIRS "$ENV{NUIO_INSTALL_DIR}/include")
> set (HDF5_INCLUDE_DIRS "$ENV{NUIO_INSTALL_DIR}/include")
> 
> 
10,11c14,15
< find_package(ABT REQUIRED)
< find_package(HDF5 REQUIRED COMPONENTS C)
---
> #find_package(ABT REQUIRED)
> #find_package(HDF5 REQUIRED COMPONENTS C)
14a19,22
> include_directories(${APT_INCLUDE_DIRS})
> 
> link_directories("$ENV{NUIO_INSTALL_DIR}/lib")
> link_libraries(hdf5 abt)
EOF

rm -rf build
mkdir build
cd build
export HDF5_DIR=$HDF5_DIR
cmake -DCMAKE_INSTALL_PREFIX=${NUIO_INSTALL_DIR} ..
make && make install

```

Install h5bench

```
cd $H5B_DIR
rm -rf build
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=${NUIO_INSTALL_DIR} \
         -DWITH_ASYNC_VOL=ON \
         -DCMAKE_C_FLAGS="-I$HDF5_DIR/include -L/$HDF5_DIR/lib"

make && make install

```

Set up shell to use shared build.  This is what is needed by all 
users.
```
export NUIO_INSTALL_DIR=/eagle/dist_relational_alg/nuio
export HDF5_DIR=$NUIO_INSTALL_DIR
export HDF5_PLUGIN_PATH=$HDF5_DIR/lib

PATH=/eagle/dist_relational_alg/nuio/bin/:$PATH
LD_LIBRARY_PATH=/eagle/dist_relational_alg/nuio/lib:$LD_LIBRARY_PATH

```

Test sync and async h5bench write tests.
```
H5FD_SUBFILING_IOC_PER_NODE=1 H5FD_IOC_THREAD_POOL_SIZE=2 h5bench --debug sync-write-1d-contig-contig-subfiling-stripe32c1m.json
```

```
h5bench --debug async-write-1d-contig-contig.json
```

