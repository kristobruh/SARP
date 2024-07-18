#!/bin/bash -l
#SBATCH --account=project_number
#SBATCH --job-name=your_job_name
#SBATCH --partition=small
#SBATCH --mem=30G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --time=4:00:00
#SBATCH --gres=nvme:20
#SBATCH --output=/path/to/your/results/folder/SLURM/%A_%a.out
#SBATCH --error=/path/to/your/results/folder/Error/%A_%a_ERROR.out
#SBATCH --mail-type=FAIL,END

# Start measuring time
start=$(date +%s)

module load snakemake
snakemake --cores 4

# End measuring time
end=$(date +%s)
runtime=$((end-start))
echo "Script execution time: $runtime seconds"
