#!/bin/bash -l
#SBATCH --account=project_2001106
#SBATCH --job-name=test_job
#SBATCH --partition=small
#SBATCH --mem=30G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --time=0:30:00
#SBATCH --gres=nvme:20
#SBATCH --output=/scratch/project_2001106/lake_timeseries/test/SLURM/%A_%a.out
#SBATCH --error=/scratch/project_2001106/lake_timeseries/test/Error/%A_%a_ERROR.out
#SBATCH --mail-type=FAIL,END

# Start measuring time
start=$(date +%s)

module load snakemake
snakemake --cores 4

# End measuring time
end=$(date +%s)
runtime=$((end-start))
echo "Script execution time: $runtime seconds"