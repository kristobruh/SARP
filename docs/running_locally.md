# Running SAPR locally

SARP is created to be used through CSC's Puhti command line interface. Running the program locally works as well, though I give no guarantees. In order to do so, you should:

1. Install all required packages. These can be found in requirements.txt. NOTE: Some packages might be missing, which you'll likely find while running the program.

2. Remove module calls. in run_interactive.sh, run_batch.sh, and Snakefile, remove all `module load` rows. This way, I believe, you can get the program to run locally as well.