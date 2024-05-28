# Sentinel-1 Automated Retrieval and Processing (SARP)

## Description
This script is an automated Sentinel-1 SAR image download, process, and analysis pipeline. The script is meant to be run from the command line interface of Puhti, either in interactive or batch mode. Running locally works as well, but then you need to ensure that you have all the packages installed, and modify the bash script by removing module calls.

This program can download and process both Ground Range Retected (GRD) and Single-look Complex (SLC) images.


## Workflow

### Input:
- Path to a shapefile containing polygon(s), or a csv or coordinates in espg:3067. This shapefile is then parsed into individual polygons, and all available images are downloaded for the overall area for the given plot. For coordinates, a small buffer is created.
- Result path: Full path to folder which is to be created and where results are stored.
- Arguments (.txt): AS file specifying download and processing parameters.

### Run:
The basic command is: run_type script_name -s source_file -r result folder -b (bulk download) -p (parse input file)'.
Source file path and results folder path are mandatory. Optional commands include:
- Bulk download -b: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, a thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately.
- Parse shapefile -p: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile.

For interactive: bash run_interactive.sh -s /path/to/shapefile/folder/ /path/to/results/folder/ -b -p
For batch: sbatch run_batch.sh /path/to/shapefile/folder/ /path/to/results/folder/

1. run_(interactive/batch).sh: Dictates the script structure and downloads necessary modules.
2. initialize.py: Creates folder structure, parses shapefile
3. download_from_asf.py: Downloads images as defined by arguments.txt from Alaska Satellite Facility (ASF). Requires an account and saving it in a .txt as:
<USERNAME> tab <PASSWORD>
It might take some time for the account to start working.
4. create_dem.py: Downloads dem from NLS virtual raster. If using other than NLS environment, you might need to modify the code by uncommenting this script and adding your own dem to the results folder.
5. s1_orbit_download: Downloads and redistributes orbit files for all downloaded files, which will be used if applyOrbitFile is enabled.
5. iterate_sar.py: Runs through each downloaded image, and if they fit the polygon, it is saved.
6. SarPipeline.py: Does the actual processing of the images, called by iterate_sar.py
7. timeseries.py: Some analytics of each polygon.

For download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.


## Examples

### Example 1: GND processing with timeseries



### Example 2: SLC processing
    
## Authors and acknowledgment
Kristofer Mäkinen
kristofer.makinen@maanmittauslaitos.fi

## License
CC 4.0

## Project status
In active development.