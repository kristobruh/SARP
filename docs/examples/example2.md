### Example 2: Batch polSAR processing

This example has the same argument file, except for `processingLevel` and `process` as `SLC` and `polSAR`, respectively.  
    
In `run_batch.sh`, these parameters are set up:


```
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
```

After submitting this, this is printed out in `/SLURM/%A_%a.out`:

```
Bulk download: true, Separate polygons: true
Shapefile processing complete. 

Authenticating...
Searching for results...
Downloading 1 images...
Download complete.
Unzipping...
Unzip done. 

Writing DEM...
DEM saved. 

Downloading orbit files...
Orbit files sorted and moved to their respective directories. 

SNAP user directory set to /scratch/project_2001106/lake_timeseries/test//snap_cache

100% done.

100% done.

100% done.

100% done.

100% done.

100% done.

100% done.

100% done.

100% done.
	Applying orbit file...
	Calibration...
	Debursting SLC...
	Polarimetric spekle filtering...
	Calculating entropy, anisotropy, and alpha...
	Calculating Stokes parameters...
	Stacking polSAR parameters...
	Terrain correction...
	Subsetting...
Writing...
Processing done. 

Sending to process: S1A_IW_SLC__1SDV_20210105T160559_20210105T160626_036005_0437E2_C385.SAFE
ID: 0040110914
Masking done.
Databases created and data saved.
Timeseries done. 

ID: 0040210843
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040424546
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040424647
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040658154
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040762026
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040782032
Masking done.
Data appended to databases.
Timeseries done. 

ID: 0040827704
Masking done.
Data appended to databases.
Timeseries done. 

Script execution time: 539 seconds

```