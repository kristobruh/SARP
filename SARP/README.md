## This script is an automated Sentinel-1 SAR image download, process, and analysis pipeline. The script is meant to be run from the command line interface of Puhti, either in interactive or batch mode. Running locally works as well, but then you need to ensure that you have all the packages installed, and modify the bash script by removing module calls.

### Required packages

#### Module geoconda 

sys
os
gc
site
subprocess
datetime
argparse
shutil
zipfile
geopandas
shapely
rasterio
numpy
scipy
matplotlib
rioxarray
xarray
csv

#### Module snap

snappy
snapista
jpy


#### Additional packages:

asf_search
pyproj
psutil


The supplementary packages are installed locally as:

try:
    import asf_search as asf
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "asf_search"])

If the code does not work after a few tries (i.e. Warning 'not on path' is given), try adding the following line to e.g. download_from_asf:
from os.path import dirname
sys.path.append(dirname())


## Workflow

Input:
- Path to a shapefile containing polygon(s). This shapefile is then parsed into individual polygons, and all available images are downloaded for the overall area for the given plot.
- Result path: Full path to folder which is to be created and where results are stored.
- Arguments (.txt): AS file specifying download and processing parameters.

Run:
For interactive: bash run_interactive.sh /path/to/shapefile/folder/ /path/to/results/folder/
For batch: sbatch run_batch.sh /path/to/shapefile/folder/ /path/to/results/folder/

1. run_(interactive/batch).sh: Dictates the script structure and downloads necessary modules.
2. initialize.py: Creates folder structure, parses shapefile
3. download_from_asf.py: Downloads images as defined by arguments.txt from Alaska Satellite Facility (ASF). Requires an account and saving it in a .txt as:
<USERNAME> tab <PASSWORD>
It might take some time for the account to start working.
4. create_dem.py: Downloads dem from NLS virtual raster. If using other than NLS environment, you might need to modify the code by uncommenting this script and adding your own dem to the results folder.
5. iterate_sar.py: Runs through each downloaded image, and if they fit the polygon, it is saved.
6. SarPipeline.py: Does the actual processing of the images, called by iterate_sar.py
7. timeseries.py: Some analytics of each polygon.

For download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.


