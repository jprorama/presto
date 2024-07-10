#!/bin/bash
#
#

# set DEBUG=1 in caller to trace
if [[ $DEBUG == 1 ]]
then
  set -x
fi

DATASET=${DATASET:-$1}
RANKS=${RANKS:-$2}
RUNS=${RUNS:-$3}
TESTS=${TESTS:-$4} # string that includes names of tests to run eg datadist_mean
BATCH_TAG=${BATCH_TAG:-$5}
H5GEN_ARGS=${H5GEN_ARGS:-$6}


HDF5_FILE=test-${PBS_JOBID}.h5

. ~/bin/set_nuio

cd ~/projects/p2

function run_bench {
  echo $@ 1>&2
  $@ 2>&1 |  awk '/SUCCESS/{print $14}' | sed -e 's/)//'
}

function clean_up {
  rm -f storage/$HDF5_FILE
}

#expdir=$1
expdir="data/experiments/${DATASET}-${RANKS}-${BATCH_TAG}"
mkdir -p $expdir
clean_up

for (( i=0; i<${RUNS}; i=$i+1 ))
do

if [[ $TESTS =~ "uniform" ]]
then
exp_name="uniform_sync_${DATASET}+n${RANKS}+r$i"
echo -n ${exp_name}": "
h5bench_script=uniform-${DATASET}-${RANKS}-h5b.json
./h5gen.py --hdf5file $HDF5_FILE  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up
fi

if [[ $TESTS =~ "normal" ]]
then
exp_name="normal_sync_${DATASET}+n${RANKS}+stdev0+r$i"
echo -n ${exp_name}": "
h5bench_script=normal-${DATASET}-${RANKS}-h5b.json
./h5gen.py --hdf5file $HDF5_FILE  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up
fi

if [[ $TESTS =~ "datadist" ]]
then
exp_name="datadist_sync_${DATASET}+n${RANKS}+interp+r$i"
echo -n ${exp_name}": "
h5bench_script=datadist-${DATASET}-${RANKS}-h5b.json
./h5gen.py --hdf5file $HDF5_FILE  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up
fi

if [[ $TESTS =~ "mean" ]]
then
exp_name="datadist_sync_${DATASET}+n${RANKS}+mean+r$i"
echo -n ${exp_name}": "
h5bench_script=datadist-${DATASET}-mean-${RANKS}-h5b.json
./h5gen.py --hdf5file $HDF5_FILE  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up
fi

done

