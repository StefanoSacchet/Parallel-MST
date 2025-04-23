#!/bin/bash
#PBS -l select=1:ncpus=1:mem=1gb
#PBS -l walltime=00:01:00
#PBS -q short_cpuQ

module load cmake-3.15.4
module load mpich-3.2

module list

