import sys, os, site, subprocess, zipfile, argparse, dask
import geopandas as gpd
from shapely.geometry import box, Point, Polygon
from datetime import date 

#install a foreign package, find it, and import
try:
    import asf_search as asf
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "asf_search"])
    import asf_search as asf




            
def unzip(dataPath, file):
    '''
    Unzip a single zip file and remove the zip file.
    
    Input:
    - zip_file_path (str) - Full path to the zip file.
    
    Output: 
    Unzipped files.
    '''
    
    # Extract the directory path without the zip extension
    extract_to = os.path.splitext(file)[0]
    
    # Unzip
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(dataPath)
    
    # Delete the zip file
    os.remove(file)


    

def read_arguments_from_file(file_path):
    '''
    Helper function to read the arguments.txt file.
    
    Input:
    - file_path (str) - Full path to the arguments file.
    
    Output: 
    arguments (dict) - Dictionary of the arguments.
    '''
    arguments = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.strip().startswith('#'):
                arg_name, arg_value = line.strip().split('\t')
                arguments[arg_name.strip()] = arg_value.strip()
    return arguments




def authenticate(pathToClient):
    '''
    Authenticates your asf account.
    
    Input:
    - pathToClient (str) - Full path to the file containing client info.
    
    Output: 
    - session - authenticated session file.
    '''
    # Authenticate your account
    with open(pathToClient, 'r') as file:
        line = file.readline().strip()
        username, password = line.split('\t')

    print('Authenticating...')
    session = asf.ASFSession().auth_with_creds(username, password)
    
    return session
    
    
    
    
def search_and_download(start,end,season,wkt_aoi,beamMode,flightDirection,polarization,processingLevel,processes,pathToResult,session):
    '''
    Searches and downloads S1 files with the given parameters.
    
    Input:
    - start (str) - Start of the observation period (e.g. 2021-03-25)
    - end (str) - End of the observation period (e.g. 2021-04-25)
    - season - Specify a time period within the search window, in DOY (e.g. '100,250')
    - wkt_aoi (str) - A wkt of the AOI.
    - beamMode (str) - Beam mode (e.g. IW, EW, SM)
    - flightDirection (str) - Flight direction, ASCENDING or DESCENDING (cannot be both).
    - polarization (str) - Desired polarization (e.g. VV,VV+VH or HH)
    - processingLevel (str) - Whether SLC or GRD (e.g. GRD_HD or SLC)
    - processes (int) - How many files are downloaded simultaneously.
    - pathToResult (str) - Full path to the result folder.
    - session - Authenticated session file.
    
    Output: 
    - Downloaded S1 files.
    '''
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
    # Read arguments from shellscript
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

    # Authenticate the session
    session = authenticate(pathToClient)
    
    # Create paths and wkt's
    if bulkDownload:
        pathToResult = os.path.join(path,'tiffs')
        filename = os.path.basename(pathToTarget)
        filename = os.path.splitext(filename)[0]
        pathToTarget = os.path.join(path,f'{filename}.shp')
        wkt_aoi = create_wkt(pathToTarget)
     
    else:
        pathToResult = os.path.join(path,identifier,'tiffs')
        wkt_aoi = create_wkt(os.path.join(path,identifier,'shapefile',f'{identifier}.shp'))
    
    
    # Download files
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
