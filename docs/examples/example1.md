### Example 1: Interactive GND processing with timeseries

This example is run with the follwing `argument.txt` parameters:

```
### DOWNLOAD PARAMETERS ###
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