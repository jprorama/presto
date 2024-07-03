#!/bin/bash
#
#

DATASET=$1
RANKS=$2
RUNS=$3
BATCH_TAG=$4
H5GEN_ARGS=$5

HDF5_FILE=storage/${PBS_JOBID}/test5-${DATASET}-${RANKS}.h5

. ~/bin/set_nuio

cd ~/projects/p2

function run_bench {
  echo $@ 1>&2
  $@ 2>&1 |  awk '/SUCCESS/{print $14}' | sed -e 's/)//'
}

function clean_up {
  rm -f $HDF5_FILE
}

#expdir=$1
expdir="data/experiments/${DATASET}-${RANKS}-${BATCH_TAG}"
mkdir -p $expdir
clean_up

for (( i=0; i<${RUNS}; i=$i+1 ))
do

exp_name="uniform_sync_${DATASET}+n${RANKS}+r$i"
echo -n ${exp_name}": "
h5bench_script=uniform-${DATASET}-${RANKS}-h5b.json
./h5gen.py --directory "storage/_${PBS_JOBID}/"  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}.${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up

exp_name="normal_sync_${DATASET}+n${RANKS}+stdev0+r$i"
echo -n ${exp_name}": "
h5bench_script=normal-${DATASET}-${RANKS}-h5b.json
./h5gen.py --directory "storage/_${PBS_JOBID}/"  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up

exp_name="datadist_sync_${DATASET}+n${RANKS}+interp+r$i"
echo -n ${exp_name}": "
h5bench_script=datadist-${DATASET}-${RANKS}-h5b.json
./h5gen.py --directory "storage/_${PBS_JOBID}/"  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up

exp_name="datadist_sync_${DATASET}+n${RANKS}+mean+r$i"
echo -n ${exp_name}": "
h5bench_script=datadist-${DATASET}-mean-${RANKS}-h5b.json
./h5gen.py --directory "storage/_${PBS_JOBID}/"  $H5GEN_ARGS ${h5bench_script}-template > ${h5bench_script}_${PBS_JOBID}
result="$(run_bench h5bench --debug ${h5bench_script}_${PBS_JOBID})"
echo ${exp_name} > ${result}/experiment
mv ${result} ${expdir}
clean_up

done

