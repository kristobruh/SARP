#!/bin/bash -l
#SBATCH --account=project_projectnumber
#SBATCH --job-name=example_job
#SBATCH --partition=small
#SBATCH --mem=50G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --time=2-23:00:00
#SBATCH --gres=nvme:35
#SBATCH --output=/path/to/results/folder/SLURM/%A_%a.out
#SBATCH --error=/path/to/results/folder/Error/%A_%a_ERROR.out
#SBATCH --mail-type=FAIL,END

# Start measuring time
start=$(date +%s)

module load snakemake
snakemake --unlock
snakemake --cores 4

# End measuring time
end=$(date +%s)
runtime=$((end-start))
echo "Script execution time: $runtime seconds"
