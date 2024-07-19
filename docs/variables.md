# Processing options

As explained before, arguments.csv is the main file for configuring your desired download, processing, and post-processing parameters. Here is a more detailed explanation of each of them.

For more detailed explanation on (some) download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.


### Download parameters

**start**
The start date of the observations. The format is YYYY-MM-DD. Example: 2021-05-01



**end**
The end date of the observations. The format is YYYY-MM-DD. Example: 2021-06-01



**season**
Whether observations are downloaded only for certain period for each year. If not desired (all available data from start to end), set to none. Example: 15,200 , or, none.



**beamMode**
Determines the beam mode of the instrument. For S1 possible options are: EW, IW, S1, S2, S3, S4, S5, S6, WV. This is often best set at IW.



**flightDirection**
Whether observations are captured from ascending or descending track. Depending on what you want, both ASCENDING and DESCENDING work. Possible options are ASC, ASCENDING, DESC, DESCENDING



**polarization**
Polarization of the images. VV,VV+VH is valid in Finland. Other options are: VV, VV+VH, Dual VV, VV+VH, Dual HV, Dual HH, HH, HH+HV, VV, Dual VH. Can include several options, separated by a comma.



**processingLevel**
Whether images are downloaded as real or imaginary. GRD_HD for Ground Range detected, SLC for complex and polSAR images.


**processes**
Amount of simultaneous downloads. 8 is good.



### Processing parameters
You can use one of three preset processing pipelines: GRD, SLC, polSAR (case sensitive). Note that for GRD, processingLevel should be set at GRD_HD, and for SLC and polSAR at SLC. Alternatively, you can set 'process' as False, and define the processing parameters yourself below.

**process**


**identifierColumn**
Name of the column which identifies each polygon. If you're not sure what your identifier column is, just run the process with some name, and the columns will be printed. Example: PLOHKO

Example processing pipelines:
GRD: applyOrbitFile, thermalNoiseRemoval, calibration, speckleFiltering, terrainCorrection, linearToDb.
SLC: slcSplit, applyOrbitFile, calibration, slcDeburst, speckleFiltering, terrainCorrection.

slcSplit	False
applyOrbitFile	False
thermalNoiseRemoval	False
calibration	False
multilook	False
complexOutput	False
slcDeburst	False
speckleFiltering	False
polarimetricSpeckleFiltering	False
filterResolution	5
polarimetricParameters	False
terrainCorrection	False
terrainResolution	10.0
bandMaths	False
bandMathsExpression	Sigma0_VV_db + 0.002
linearToDb	False



### Post-processing parameters
timeseries	True

Whether several images are averaged in timeseries analysis. Usually should be set at False, unless you know you want to average images.
movingAverage	False
movingAverageWindow	2

If reflector is enabled, the code finds a brightest spot in the image and calculates timeseries on that one spot.
reflector	False

Weather analysis is currently disabled.
downloadWeather	False
