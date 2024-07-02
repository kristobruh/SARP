# Sentinel-1 Automated Retrieval and Processing (SARP)

## Description
This package is an automated Sentinel-1 SAR image download, process, and analysis pipeline for SAR images in Finland. The package is run from the command line interface of Puhti, either in interactive or batch mode. Running locally works as well, but then you need to ensure that you have all the packages installed, and modify the bash script by removing module calls.

This program can download and process both Ground Range Detected (GRD) and Single-look Complex (SLC) images. Additionally, polSAR image processing is possible as well.

Processing times are roughly:
- Download GRD_HD, per 8 images: 
- Download SLC, per 8 images:
- Processing GRD_HD, per image:
- Processing SLC, per image:
- Timeseries, per target: A few seconds.

## Dependencies
This program is configured for CSC's Puhti environment. As such, it uses modules _geoconda_ and _snap_, along with a few external packages that are installed locally. The packages are:

- fmiopendata
- asf_search
- download_eofs
- 
-



## Workflow

### 1. Clone repository
Use `git clone https://gitlab.com/fgi_nls/kauko/chade/sarp.git` to clone the repository to a destination of your liking.

### 2. Set up input shapefile
You can use `example_target.gpkg` to try out the script, or use your own target.

### 3. Configure arguments
In `arguments.txt`,set up your preferred arguments. It is good to start with a short timeframe, e.g. 10 days and `GRD_HD` processing processingLevel and GRD as `process``, to configure the packages. See the file for more descriptions on the parameters. Note: If you use a predefined process, there is no need to define the individual parameters separately. 

### 4. Run:
To run, you need to navigate to /sarp/SARP/. The basic command is: 

```<run type> <script name> -s <source file> -r <result folder> -b (bulk download) -p (parse input file) ```

Source file path and results folder path are mandatory. Optional commands include:
- Bulk download `-b`: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, a thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately.
- Parse shapefile `-p`: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile.

**Interactive**

Before running the script in interactive, start a new job by `sinteractive -i`, and set up your parameters. The script is partly parallelized, so several cores is recommended, and at least 12GB of memory.

Example for running interactive: 

`bash run_interactive.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/ -b -p `



**Batch**

`sbatch run_batch.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/  -b -p`

If you run the script in batch process mode, remember to set up the batch process paramters in `run_batch.sh`. It is recommended to first run it in interactive to ensure that all works.


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

Then, navigate to `sarp/SARP/` and call the script from CLI:

`bash run_interactive.sh -s /path/to/shapefile/folder/example_target.gpkg -r /path/to/results/folder/example -b -p `

After this the script will run uninterrupted:

```
Bulk download: true, Separate polygons: true
------------------------------------------
Geoconda 3.10.9, GIS libraries for Python
https://docs.csc.fi/apps/geoconda
------------------------------------------
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

### Example 2: Batch SLC processing
    
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


### Input:
- Path to a shapefile containing polygon(s), or a csv or coordinates in espg:3067. This shapefile is then parsed into individual polygons, and all available images are downloaded for the overall area for the given plot. For coordinates, a small buffer is created.
- Result path: Full path to folder which is to be created and where results are stored.
- Arguments (.txt): AS file specifying download and processing parameters. For more detailed explanation on download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.


## Authors and acknowledgment
Kristofer Mäkinen

kristofer.makinen@maanmittauslaitos.fi

When publishing, additional credit should be given to the creators of asf_search and download_eofs.

## License
CC 4.0

## Project status
In active development.