# NOTE: for more explanation on the code, see ASF_download.ipynb.

# Example call from command line:

#python download_from_asf.py --pathToResult /scratch/project_2001106/lake_timeseries/test_download/ --pathToClient /users/kristofe/access/asf_client.txt --pathToShapefile /scratch/project_2001106/lake_timeseries/lake.shp --start 2022-01-01 --end 2022-02-01 --season 20 100 --beamMode IW --flightDirection ASCENDING --polarization VV,VV+VH --processingLevel GRD_HD --processes 1



# Import necessary packages
import sys
import site
import os
import subprocess
import zipfile

#install a foreign package, find it, and import
try:
    import asf_search as asf
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "asf_search"])
    import asf_search as asf

import geopandas as gpd
from shapely.geometry import box, Point, Polygon
from datetime import date 
import argparse
import dask



            
def unzip(dataPath, file):
    """
    Unzip a single zip file and remove the zip file.
    
    Input:
    - zip_file_path (str): Full path to the zip file.
    
    Output: 
    Unzipped files.
    """
    
    # Extract the directory path without the zip extension
    extract_to = os.path.splitext(file)[0]
    
    # Unzip
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(dataPath)
    
    # Delete the zip file
    os.remove(file)


    

def read_arguments_from_file(file_path):
    arguments = {}
    with open(file_path, 'r') as file:
        for line in file:
            arg_name, arg_value = line.strip().split('\t')
            arguments[arg_name.strip()] = arg_value.strip()
    return arguments




def authenticate(pathToClient):
    # Authenticate your account
    with open(pathToClient, 'r') as file:
        line = file.readline().strip()
        username, password = line.split('\t')

    print('Authenticating...')
    session = asf.ASFSession().auth_with_creds(username, password)
    
    return session
    
    
    
    
def search_and_download(start,end,season,wkt_aoi,beamMode,flightDirection,polarization,processingLevel,processes,pathToResult,session):
    
    #search for the results
    print('Searching for results...')
    results = asf.search(
        platform=asf.PLATFORM.SENTINEL1A,
        #processingLevel=[asf.PRODUCT_TYPE.SLC],
        start=start,
        end=end,
        season=season, # beginning of october to end of may #[274,152]
        intersectsWith=wkt_aoi,
        beamMode=beamMode,
        flightDirection=flightDirection,
        polarization=polarization,
        processingLevel=processingLevel
        )
    # ['GRD_HS', 'GRD_HD', 'GRD_MS', 'GRD_MD', 'GRD_FD']
    ### Save Metadata to a Dictionary
    metadata = results.geojson()

    print(f'Downloading {len(results)} images...')

    if not os.path.exists(pathToResult):
            os.makedirs(pathToResult)

    results.download(
         path = pathToResult,
         session = session, 
         processes = processes 
      )   

    print('Download complete.')
    
    
    
def create_wkt(pathToTarget):
    # Create a rectangle around the target
    gdf = gpd.read_file(pathToTarget)

    # Ensure the shapefile is wgs84
    crs = gdf.crs
    if crs != 'EPSG:4326':
        # Reproject geometry to WGS84 (EPSG:4326)
        gdf = gdf.to_crs(epsg=4326)

    bounds = None

    for index, row in gdf.iterrows():
        polygon_bounds = row.geometry.bounds
        if bounds is None:
            bounds = polygon_bounds
        else:
            bounds = (
                min(bounds[0], polygon_bounds[0]),
                min(bounds[1], polygon_bounds[1]),
                max(bounds[2], polygon_bounds[2]),
                max(bounds[3], polygon_bounds[3])
            )


    gdf_bounds = gpd.GeoSeries([box(*bounds)])
    wkt_aoi = gdf_bounds.to_wkt().values.tolist()[0]
    
    return wkt_aoi




def main():
    
    # Extract arguments from bash
    # First argument: source path
    # Second: result path
    # Third argument: bulk download
    pathToTarget = sys.argv[1]
    path = sys.argv[2]
    bulkDownload = sys.argv[3].lower() == 'true'
    if not bulkDownload:
        identifier = sys.argv[4]

    # Read arguments from the text file
    args = read_arguments_from_file(os.path.join(os.getcwd(), 'arguments.txt'))
    pathToClient = args.get('pathToClient')
    start = args.get('start')
    end = args.get('end')
    season = args.get('season')
    if season != 'none':
        season = list(map(int, season.split()))
    else:
        season = []
    beamMode = args.get('beamMode')
    flightDirection = args.get('flightDirection')
    polarization = args.get('polarization')
    processingLevel = args.get('processingLevel')
    processes = int(args.get('processes'))

    session = authenticate(pathToClient)
    
    if bulkDownload:
        pathToResult = os.path.join(path,'tiffs')
        filename = os.path.basename(pathToTarget)
        filename = os.path.splitext(filename)[0]
        pathToTarget = os.path.join(path,f'{filename}.shp')
        wkt_aoi = create_wkt(pathToTarget)
     
    else:
        pathToResult = os.path.join(path,identifier,'tiffs')
        wkt_aoi = create_wkt(os.path.join(path,identifier,'shapefile',f'{identifier}.shp'))
    
    
    
    search_and_download(start,end,season,wkt_aoi,beamMode,flightDirection,
                            polarization,processingLevel,processes,pathToResult,session)


    # ------- START UNZIP -------

    sorted_files = sorted(os.listdir(pathToResult))

     # Create list of delayed functions
    list_of_delayed_functions = []

    print("Unzipping...")
    # Loop through folders
    for file in sorted_files:
        result = dask.delayed(unzip)(pathToResult,os.path.join(pathToResult,file))
        # Append the list of delayed functions
        list_of_delayed_functions.append(result)

    # Execute delayed computations
    dask.compute(list_of_delayed_functions)
    print("Unzip done. \n")
    # ------- END UNZIP --------
    
if __name__ == "__main__":
    main()
