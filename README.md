# Sentinel-1 Automated Retrieval and Processing (SARP)

## Description
This package is an automated Sentinel-1 SAR image download, process, and analysis pipeline for SAR images in Finland. The script is run from the command line interface of Puhti, either in interactive or batch mode. (Running locally might work as well, but then you need to ensure that you have all the packages installed, and modify the bash script by removing module calls. Thus, I recommed using Puhti's CLI.) 

This program can download and process both Ground Range Detected (GRD) and Single-look Complex (SLC) images. Additionally, polSAR image processing is possible.

The outputs of this program are:
- Processed, masked SAR images for the entire target (if -b is enabled, more on that later) and/or for each polygon separately (if -p is enabled)
- A .csv file of all bands' mean values, for each target polygon as well as all targets in one .csv. For GRD, min, max, and std values are saved as well.
- An SQL database of all target's band values, along with ID, orbit, processingLevel, look direction, and pixel count info.
- Shapefiles of the targets
- A 2m DEM and shapefile(s) of the target area(s)
- Optional benchmark file

## Dependencies
This program is configured for CSC's Puhti environment. As such, it uses modules _geoconda_ and _snap_, along with a few external packages that are installed locally. The packages are:

- fmiopendata
- asf_search
- download_eofs

**NOTE:** You also need to create an EarthData account and verify it in order to download images from **ASF** (Alaska Satellite Facility). It might take some time for the verification to take effect. You can do it at:
https://asf.alaska.edu/how-to/data-basics/get-started-with-an-earthdata-login-account/
After making your account, save the login info (username, password, separated by a tab) to a .txt file and save it somewhere where it can be accessed (I recommend user folder for privacy).


## Workflow

There are two options the program can be ran through: regular **command line run**, and **Snakemake**. Regular CLI run is somewhat more straightforward, but is prone to errors caused by e.g. internet connection breakage, and is slower especially on large datasets and target areas. Snakemake, on the other hand, offers complete parallellization and significantly higher processing speeds, which is useful in long timeseries. Additionally, snakemake creates 'checkpoints', which means that an error does not require restarting the entire process, and automatic retries attempt to complete the process. The setup is mostly the same, execpt for the last part, when the scirpt run is called.

### 1. Clone repository
Use `git clone https://gitlab.com/fgi_nls/kauko/chade/sarp.git` to clone the repository to a destination of your liking.

### 2. Set up input shapefile
You can use `example_target.gpkg` to try out the script, or use your own target. .shp and .gpgk files, as well as coordinate csv's, are accepted as input.

### 3. Configure arguments
In `arguments.txt`,set up your preferred arguments. It is good to start with a short timeframe, e.g. 10 days and `GRD_HD` processing processingLevel and GRD as `process``, to configure the packages. See the file for more descriptions on the parameters. Note: If you use a predefined process, there is no need to define the individual parameters separately. 

For more detailed explanation on download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.

Initially you might need to run the script a couple times to get the packages working.

### 4a. Run using CLI:
To run, you need to navigate to sarp/scripts/. The basic command is: 

```<run type> <script name> -s <source file> -r <result folder> -b (bulk download) -p (parse input file) ```

Source file path and results folder path are mandatory. Optional commands include:
- Bulk download `-b`: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, a thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately.
- Parse shapefile `-p`: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile. Usually it is wise to enable this for individual parcel analysis.

**Interactive**

Before running the script in interactive, start a new job by `sinteractive -i`, and set up your parameters. The script is partly parallelized, so several cores is recommended, and at least 12GB of memory.

Example for running interactive: 

`bash run_interactive.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/ -b -p `



**Batch**

`sbatch run_batch.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/  -b -p`

If you run the script in batch process mode, remember to set up the batch process paramters in `run_batch.sh`. It is recommended to first run it in interactive to ensure that all works.

For some example commands, see **command.txt**.


### 4b. Run using Snakemake:
Again, navigate to sarp/scripts/. Set up the input parameters (source, target directory, bulk processing, separating) in config.yaml found in the folder. After that, in your CLI either write:

`module load snakemake`

`snakemake --cores 4`

for interactive process, or:

`sbatch run_batch_snakemake.sh`

for batch processing. Just remember to configure that batch process file parameters the same way as in regular batch processing.

## Examples

### Example 1: Interactive GND processing with timeseries

This example is run with the follwing `argument.txt` parameters:

```### DOWNLOAD PARAMETERS ###
# Add the full path to your ASF credentials file. The file should be a .txt with one row, with structure : username<tab>password .
pathToClient	/users/kristofe/access/asf_client.txt
start	2021-01-01
end	2021-01-10

# Preferred season, eg: 15,200. If not desired, set to none.
season	none

# This is often best set at IW.
beamMode	IW

# Depending on what you want, both ASCENDING and DESCENDING work.
flightDirection	ASCENDING

# VV,VV+VH is valid in Finland.
polarization	VV,VV+VH

# GRD_HD for Ground Range detected, SLC for complex and polSAR images.
processingLevel	GRD_HD

# Amount of simultaneous downloads. 8 is good.
processes	8



### PROCESSING PARAMETERS ###

# You can use one of three preset processing pipelines: GRD, SLC, polSAR.
# Alternatively, you can set it at False, and define the processing parameters yourself.
# If you're not sure what yor identifier column is, just run the process with some name, and the columns will be printed.

process	GRD
identifierColumn	PLOHKO

#########

# NOTE: slcSplit and slcDeburst only apply for SLC images.
# Example processing pipelines:
# GRD: applyOrbitFile, thermalNoiseRemoval, calibration, speckleFiltering, terrainCorrection, linearToDb.
# SLC: slcSplit, applyOrbitFile, calibration, slcDeburst, speckleFiltering, terrainCorrection.

slcSplit	True
applyOrbitFile	True
thermalNoiseRemoval	False
calibration	True
complexOutput	True
slcDeburst	False
speckleFiltering	False
polarimetricSpeckleFiltering	False
filterResolution	5
polarimetricParameters	True
terrainCorrection	False
terrainResolution	10.0
bandMaths	False
bandMathsExpression	Sigma0_VV_db + 0.002
linearToDb	False

#########


### POST-PROCESSING PARAMETERS ###
timeseries	True

movingAverage	False
movingAverageWindow	2

# If reflector is enabled, the code finds a brightest spot in the image and calculates timeseries on that one spot.
reflector	False
downloadWeather	False

```

Then, navigate to `sarp/scripts/` and call the script from CLI:

`bash run_interactive.sh -s /path/to/shapefile/folder/example_target.gpkg -r /path/to/results/folder/example -b -p `

After this the script will run uninterrupted:

```
Bulk download: true, Separate polygons: true

Ensuring all external packages are installed...
All good!

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

Sending to process: S1A_IW_GRDH_1SDV_20210105T160601_20210105T160626_036005_0437E2_A884.SAFE

        Applying orbit file...

100% done.
        Thermal noise removal...

100% done.
        Calibration...

100% done.
        Speckle filtering...

100% done.
        Terrain correction...

100% done.
        To dB...

100% done.
        Subsetting...

100% done.
Writing...
Processing done.

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

Script execution time: 117 seconds

```

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

### Example 3: PolSAR processing in Snakemake, interactive

This example uses the same inputs as example 2, so arguments.txt remains the same. The only change is done to sarp/config.yaml, where the input arguments ae set up:

```
source_path: "/path/to/shapefile/folder/example_target.gpkg"
data_path: "/path/to/results/folder/example"
separate: true
bulk_download: true
restart-times: 3
```

Then, the process is called:

`module load snakemake`

`snakemake --cores 4`.

This then prints out the dependencies and working order, and proceeds to complete them as needed:


```
Assuming unrestricted shared filesystem usage.
Building DAG of jobs...
Using shell: /usr/bin/bash
Provided cores: 4
Rules claiming more threads will be scaled down.
Job stats:
job                     count
--------------------  -------
aggregate_benchmarks        1
all                         1
create_timeseries           1
download_dem                1
download_images             1
download_orbits             1
initialize                  1
process_images              1
total                       8

Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:20:18 2024]
localrule initialize:
    input: initialize.py
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    jobid: 3
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Shapefile processing complete.

[Mon Jul 15 11:20:26 2024]
Finished job 3.
1 of 8 steps (12%) done
Select jobs to execute...
Execute 2 jobs...

[Mon Jul 15 11:20:26 2024]
localrule download_images:
    input: download_images.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt
    jobid: 4
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


[Mon Jul 15 11:20:26 2024]
localrule download_dem:
    input: download_dem.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt
    jobid: 5
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Writing DEM...
DEM saved.

[Mon Jul 15 11:20:31 2024]
Finished job 5.
2 of 8 steps (25%) done
Authenticating...
Searching for results...
Downloading 1 images...
Download complete.
Unzipping...
Unzip done.

[Mon Jul 15 11:24:17 2024]
Finished job 4.
3 of 8 steps (38%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:24:17 2024]
localrule download_orbits:
    input: download_orbits.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt
    jobid: 6
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Downloading orbit files...
Orbit files sorted and moved to their respective directories.

[Mon Jul 15 11:24:33 2024]
Finished job 6.
4 of 8 steps (50%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:24:33 2024]
localrule process_images:
    input: process_images_snakemake.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    jobid: 2
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

Lock acquired.
        Applying orbit file...

100% done.
Lock released.
        Calibration...

100% done.
        Debursting SLC...

100% done.
        Polarimetric spekle filtering...

100% done.
        Calculating entropy, anisotropy, and alpha...

100% done.
        Calculating Stokes parameters...

100% done.
        Stacking polSAR parameters...

100% done.
        Terrain correction...

100% done.
        Subsetting...

100% done.
Writing...
Processing done.

All tasks completed.
[Mon Jul 15 11:25:29 2024]
Finished job 2.
5 of 8 steps (62%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:25:29 2024]
localrule create_timeseries:
    input: timeseries.py, /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt
    jobid: 1
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

Data path: /scratch/project_2001106/lake_timeseries/test/
------------------------------------------
Geoconda 3.10.9, GIS libraries for Python
https://docs.csc.fi/apps/geoconda
------------------------------------------
0040110914
Masking done.
Databases created and data saved.
Timeseries done.

0040210843
Masking done.
Data appended to databases.
Timeseries done.

0040424546
Masking done.
Data appended to databases.
Timeseries done.

0040424647
Masking done.
Data appended to databases.
Timeseries done.

0040658154
Masking done.
Data appended to databases.
Timeseries done.

0040762026
Masking done.
Data appended to databases.
Timeseries done.

0040782032
Masking done.
Data appended to databases.
Timeseries done.

0040827704
Masking done.
Data appended to databases.
Timeseries done.

[Mon Jul 15 11:26:06 2024]
Finished job 1.
6 of 8 steps (75%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:26:06 2024]
localrule aggregate_benchmarks:
    input: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    jobid: 7
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

[Mon Jul 15 11:26:24 2024]
Finished job 7.
7 of 8 steps (88%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:26:24 2024]
localrule all:
    input: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    jobid: 0
    reason: Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

[Mon Jul 15 11:26:24 2024]
Finished job 0.
8 of 8 steps (100%) done
Complete log: .snakemake/log/2024-07-15T112018.437700.snakemake.log

```


## Authors and acknowledgment
Kristofer Mäkinen

kristofer.makinen@maanmittauslaitos.fi

When publishing, additional credit should be given to the creators of asf_search and download_eofs.

## License
CC 4.0

## Project status
In active development.