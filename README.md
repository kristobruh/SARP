# Sentinel-1 Automated Retrieval and Processing (SARP)

## Description
This script is an automated Sentinel-1 SAR image download, process, and analysis pipeline. The script is meant to be run from the command line interface of Puhti, either in interactive or batch mode. Running locally works as well, but then you need to ensure that you have all the packages installed, and modify the bash script by removing module calls.

This program can download and process both Ground Range Retected (GRD) and Single-look Complex (SLC) images.


## Workflow

### Input:
- Path to a shapefile containing polygon(s), or a csv or coordinates in espg:3067. This shapefile is then parsed into individual polygons, and all available images are downloaded for the overall area for the given plot. For coordinates, a small buffer is created.
- Result path: Full path to folder which is to be created and where results are stored.
- Arguments (.txt): AS file specifying download and processing parameters. For more detailed explanation on download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.

### Run:
The basic command is: 

```<run type> <script name> -s <source file> -r <result folder> -b (bulk download) -p (parse input file) ```

Source file path and results folder path are mandatory. Optional commands include:
- Bulk download -b: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, a thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately.
- Parse shapefile -p: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile.

Example for running interactive: 

``` bash run_interactive.sh -s /path/to/shapefile/folder/ /path/to/results/folder/ -b -p ```

For batch:

``` sbatch run_batch.sh /path/to/shapefile/folder/ /path/to/results/folder/ ```

### Process:
0. download_packages.py: Downloads all packages that are not native to _geoconda_. For SNAP, additional downloading will be done later. If the process fails on first try, run it again after the packages have been downloaded.
1. run_(interactive/batch).sh: Dictates the script structure and loads necessary modules.
2. initialize.py: Creates folder structure, parses shapefile or coodinate csv file.
3. download_from_asf.py: Downloads images as defined by arguments.txt from Alaska Satellite Facility (ASF). Requires a verified (but free) account.
It might take some time for the account to start working.
4. create_dem.py: Downloads dem from NLS virtual raster. If using other than NLS environment, you might need to modify the code by uncommenting this script and adding your own dem to the results folder.
5. s1_orbit_download: Downloads and redistributes orbit files for all downloaded files, which will be used if applyOrbitFile is enabled.
6. iterate_sar.py: Runs through each downloaded image, and if they fit the polygon, it is saved.
7. SarPipeline.py: Does the actual processing of the images, called by iterate_sar.py
8. timeseries.py: Some analytics of each polygon.


## Examples

### Example 1: GND processing with timeseries

Argument file:

```### DOWNLOAD PARAMETERS ###
# Add the full path to your ASF credentials file. The file should be a .txt with one row, with structure : username<tab>password .
pathToClient	/users/kristofe/access/asf_client.txt
start	2021-06-01
end	2021-06-20
# Preferred season, eg: 15,200. If not desired, set to none.
season	none
beamMode	IW
flightDirection	ASCENDING
polarization	VV,VV+VH
# SLC for complex images, or GRD_HD for ground range detected images.
processingLevel	GRD_HD
processes	8



### PROCESSING PARAMETERS ###
# NOTE: slcSplit and slcDeburst only apply for SLC images.
# Usual processing pipelines:
# GRD: applyOrbitFile, thermalNoiseRemoval, calibration, speckleFiltering, terrainCorrection, linearToDb.
# SLC: slcSplit, applyOrbitFile, calibration, slcDeburst, speckleFiltering, terrainCorrection.

slcSplit	False
applyOrbitFile	True
thermalNoiseRemoval	True
calibration	True
slcDeburst	False
speckleFiltering	True
filterResolution	3
terrainCorrection	True
terrainResolution	10.0
bandMaths	False
bandMathsExpression	Sigma0_VV_db + 0.002
linearToDb	True




### POST-PROCESSING PARAMETERS
timeseries	True
movingAverage	False
movingAverageWindow	2

```

Then the next step is to modify the _run_batch.sh_ parameters to match the output folder, processing duration, etc. (first rows):

```#!/bin/bash -l
#SBATCH --account=project_2001106
#SBATCH --job-name=example_job
#SBATCH --partition=small
#SBATCH --mem=30G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --time=6:00:00
#SBATCH --gres=nvme:20
#SBATCH --output=/scratch/project_2001106/lake_timeseries/example/SLURM/%A_%a.out
#SBATCH --error=/scratch/project_2001106/lake_timeseries/example/Error/%A_%a_ERROR.out
#SBATCH --mail-type=FAIL,END
```

After that, navigate to _sarp_ folder, and run from CLI:

``` bash run_interactive.sh -s /scratch/project_2001106/lake_timeseries/shapefile/example_shapefile.shp /scratc/project_2001106/lake_timeseries/example/ -b -p ```

After this the script will run uninterrupted:

```
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

Sending to process: S1A_IW_SLC__1SDV_20210602T153342_20210602T153409_038163_04810F_3B7D.SAFE
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
        Subsetting...

100% done.
Writing...
Processing done.
```

### Example 2: SLC processing
    
Argument file:

```### DOWNLOAD PARAMETERS ###
# Add the full path to your ASF credentials file. The file should be a .txt with one row, with structure : username<tab>password .
pathToClient	/users/kristofe/access/asf_client.txt
start	2021-06-01
end	2021-06-05
# Preferred season, eg: 15,200. If not desired, set to none.
season	none
beamMode	IW
flightDirection	ASCENDING
polarization	VV,VV+VH
# SLC for complex images, or GRD_HD for ground range detected images.
processingLevel	SLC
processes	8



### PROCESSING PARAMETERS ###
# NOTE: slcSplit and slcDeburst only apply for SLC images.
# Usual processing pipelines:
# GRD: applyOrbitFile, thermalNoiseRemoval, calibration, speckleFiltering, terrainCorrection, linearToDb.
# SLC: slcSplit, applyOrbitFile, calibration, slcDeburst, speckleFiltering, terrainCorrection.

slcSplit	True
applyOrbitFile	True
thermalNoiseRemoval	False
calibration	True
slcDeburst	True
speckleFiltering	True
filterResolution	3
terrainCorrection	True
terrainResolution	10.0
bandMaths	False
bandMathsExpression	Sigma0_VV_db + 0.002
linearToDb	False




### POST-PROCESSING PARAMETERS
timeseries	False
movingAverage	False
movingAverageWindow	2

```

## Authors and acknowledgment
Kristofer Mäkinen

kristofer.makinen@maanmittauslaitos.fi

## License
CC 4.0

## Project status
In active development.