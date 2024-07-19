# Processing options

As explained before, arguments.csv is the main file for configuring your desired download, processing, and post-processing parameters. Here is a more detailed explanation of each of them.

For more detailed explanation on (some) download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.


## Download parameters

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



## Processing parameters

Example processing pipelines:
GRD: applyOrbitFile, thermalNoiseRemoval, calibration, speckleFiltering, terrainCorrection, linearToDb.
SLC: slcSplit, applyOrbitFile, calibration, slcDeburst, speckleFiltering, terrainCorrection.

**process**
A predefined set of processing parameters. The options are either GRD, SLC, or polSAR. Very useful if you're not certain what parameters to set, and just want ready images.


**identifierColumn**
Name of the column which identifies each polygon. If you're not sure what your identifier column is, just run the process with some name, and the columns will be printed. Example: PLOHKO

**slcSplit**
Splits an SLC image to subswaths which overlap with the area. A crucial step in desktop SNAP due to it's massive reduction in size, but I don't think it's necessary in API application.


**applyOrbitFile**
Applies the precise ephemeris data from a separately downloaded satellite orbit file. Not absolutely necessary in GRD processing, but increases accuracy nevertheless. A crucial step for SLC and PolSAR processing.

**thermalNoiseRemoval**
Removes thermal noise from images. Increases resolution of GRD images, a good step to have.

**calibration**
Calibration of images from intensity values to real values, either in Sigma0 or complex output.


**complexOutput**
Whether calibration output is Sigma0 (False) or complex (True). Generally, Sigma0 is good for GRD, while complex for SLC.

**multilook**
Produces square pixels from SLC images. Good option to have, if you aim to visually inspect SLC images.

**slcDeburst**
Debursts SLC images, removing much noise. Very useful for SLC.


**speckleFiltering**
Removes noise from GRD images.


**polarimetricSpeckleFiltering**
Removes noise from SLC images, used in polSAR.


**filterResolution**
How many pixels are used in speckle filtering. The higher the number the less speckle, but the cloudier the image becomes. Generally used value is 3 to 5. (Needs to be odd)


**polarimetricParameters**
Calculates entropy, anisotropy, etc.. for polSAR.


**terrainCorrection**
Ties the image to the terrain, giving it proper placement and shape.


**terrainResolution**
Resolution at which the tie is done. Using resolution below 10m is not necessary, as the resolution of SAR is 10m.


**bandMaths**
If you want to calculate something, set this as True.


**bandMathsExpression**
The actual expression. You have to know the band name, e.g. Sigma0_VV_db. Alternatively, you can do any of the calculations yourself afterwards.


**linearToDb**
Whether the linear values are converted to db. The standard in SAR is to represent the values in logartihmic db.



## Post-processing parameters
**timeseries**
If this is disabled, masking and database creation is not done. Thus, the images are only processed, and nothing more.


**movingAverage**
Whether several images are averaged in timeseries analysis. Usually should be set at False, unless you know you want to average images.


**movingAverageWindow**
How many images you want to average. 


**reflector**
If reflector is enabled, the code finds a brightest spot in the image and calculates timeseries on that one spot.



**downloadWeather**
Weather analysis is currently disabled.