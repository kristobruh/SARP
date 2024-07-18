# Welcome to SARP Documentation

Welcome to the SARP project documentation! This page includes the full description of SARP, how to install it properly, and how to run different configurations.

SARP (Sentinel-1 Automated Retrieval and Processing) is an automated Sentinel-1 SAR image download, process, and analysis pipeline for SAR images in Finland. The script is run from the command line interface of Puhti, either in interactive or batch mode.

This program can download and process both Ground Range Detected (GRD) and Single-look Complex (SLC) images. Additionally, polSAR image processing is possible.

The outputs of this program are:
- Processed, masked SAR images for the entire target (if -b is enabled, more on that later) and/or for each polygon separately (if -p is enabled)

- A .csv file of all bands' mean values, for each target polygon as well as all targets in one .csv. For GRD, min, max, and std values are saved as well.

- An SQL database of all target's band values, along with ID, orbit, processingLevel, look direction, and pixel count info.

- Shapefiles of the targets

- A 2m DEM and shapefile(s) of the target area(s)

- Optional benchmark file

## Table of Contents

- [Introduction](introduction.md)
- [Setup](setup.md)
- [Examples](examples.md)
- [Troubleshooting](troubleshooting.md)

![Test Image](images/test_image.png)