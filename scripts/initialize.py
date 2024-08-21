import sys, os, signal, csv, subprocess
from datetime import datetime
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def process_shapefiles(source_path, result_path, identifierColumn, separate=False, bulkDownload=False):
    '''
    Read shapefile and organize them to correct folders. Optionally parse the shapefile to individual polygons.
    
    Input:
    source_path (str) - Full path to the shapefile.
    result_path (str) - Full path to the results folder.
    separate (boolean) - Whether the shapefile is parsed to polygons. Default is false.
    bulkDownload (boolean) - Whether the SAR images are downloaded individually or in bulk. Affects folder structure.
    
    Output:
    Folder structure for the next steps.
    ''' 
        
    gdf = gpd.read_file(source_path)
    
    if separate:
        for index, row in gdf.iterrows():
            # Create folder name based on the 'id' column, might be needed to change based on shapefile attributes.
            try:
                folder_name = str(row[identifierColumn])
            except KeyError:
                print(f"Error: Column identifier '{identifierColumn}' not found in the file. Possible identifier columns are: {list(gdf.columns)}.")
                parent_pid = os.getppid()
                os.kill(parent_pid, signal.SIGTERM)
                sys.exit(1)
            folder_shapefile = os.path.join(result_path, folder_name, 'shapefile')
            os.makedirs(folder_shapefile, exist_ok=True)

            # Save the polygon as a shapefile in the folder
            polygon_shapefile_path = os.path.join(folder_shapefile, f'{folder_name}.shp')
            row_gdf = gpd.GeoDataFrame([row], crs=gdf.crs)
            row_gdf.to_file(polygon_shapefile_path)

    else:
        filename = os.path.basename(source_path)
        filename = os.path.splitext(filename)[0]
        folder_shapefile = os.path.join(result_path, filename, 'shapefile')
        os.makedirs(folder_shapefile, exist_ok=True)
        gdf.to_file(os.path.join(folder_shapefile, f'{filename}.shp'))
        
    if bulkDownload:
        filename = os.path.basename(source_path)
        filename = os.path.splitext(filename)[0]
        gdf.to_file(os.path.join(result_path,f'{filename}.shp'))
            
            
def process_coordinates(input_csv, result_path, bulkDownload=False):
    '''
    Read coordinates file, create buffered shapefiles and organize them to correct folders. The coordinates are treated as individual shapefiles.
    
    Input:
    input_csv (str) - Full path to the coordinates csv.
    result_path (str) - Full path to the results folder.
    bulkDownload (boolean) - Whether the SAR images are downloaded individually or in bulk. Affects folder structure.
    
    Output:
    Folder structure for the next steps.
    ''' 
    df = pd.read_csv(input_csv, delimiter='\t', header=0)

    # Convert the DataFrame to GeoDataFrame by creating Point geometries
    df['geometry'] = df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    
    # Convert to a GeoDataFrame and set the CRS
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf = gdf.set_crs('epsg:4326')  # Set the initial CRS to WGS 84
    gdf = gdf.to_crs('epsg:3067')  # Convert to the desired CRS (EPSG 3067)


    # Iterate through each row and save the buffered point in its own folder
    for index, row in gdf.iterrows():
        # Create folder name based on the index
        folder_name = str(row['name'])
        folder_path = os.path.join(result_path, folder_name, 'shapefile')
        os.makedirs(folder_path, exist_ok=True)

        # Create a buffered polygon from the point
        point = row['geometry']

        buffer_distance=500
        buffered_polygon = point.buffer(buffer_distance)

        # Save the buffered polygon as a shapefile in the folder
        polygon_gdf = gpd.GeoDataFrame(geometry=[buffered_polygon], crs='epsg:3067')
        polygon_shapefile_path = os.path.join(folder_path ,f'{folder_name}.shp')
        polygon_gdf.to_file(polygon_shapefile_path)
        
        # Save the point as a separate shapefile
        header = "NAME\tLAT\tLONG\n"
        txt_file_path = os.path.join(folder_path, f'{folder_name}_point.txt')
        with open(txt_file_path, 'w') as txt_file:
            txt_file.write(header)
            txt_file.write(f'{folder_name}\t{row["lat"]}\t{row["lon"]}')

    
    if bulkDownload:
        filename = os.path.basename(input_csv)
        filename = os.path.splitext(filename)[0]
        
        if len(gdf) == 1:
            buffer_distance=500
            point = gdf.geometry.iloc[0]
            buffered_polygon = point.buffer(buffer_distance)
            polygon_gdf = gpd.GeoDataFrame(geometry=[buffered_polygon], crs='epsg:3067')
            polygon_gdf.to_file(os.path.join(result_path,f'{filename}.shp'))
        
        
        else:
            gdf.to_file(os.path.join(result_path,f'{filename}.shp'))

   
def read_arguments_from_file(file_path):
    '''
    Helper function to read the arguments.csv file.
    
    Input:
    - file_path (str) - Full path to the arguments file.
    
    Output: 
    arguments (dict) - Dictionary of the arguments.
    '''
    arguments = {}
    try:
        with open(file_path, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            for row in reader:
                if row and not row[0].startswith('#'):
                    arg_name, arg_value = row
                    arguments[arg_name.strip()] = arg_value.strip()
        return arguments        

    except:
        print('Error in reading arguments from file. Ensure that they are separated by a tab and you have the file in a correct path.')
            
def check_processing_parameters():
    error = None
    args = read_arguments_from_file(os.path.join(os.path.dirname(os.getcwd()), 'arguments.csv'))
    
    # Check is client path exists
    try:
        netrc_path = os.path.expanduser('~/.netrc')
        with open(netrc_path, 'r') as file:
            lines = file.readlines()
    
            if len(lines) < 3:
                raise ValueError("The .netrc file does not have enough lines to extract login and password")
                error = True
            line1 = lines[0].strip()
            if line1 != 'machine urs.earthdata.nasa.gov':
                print('The first row should be exactly "machine urs.earthdata.nasa.gov". The second row should be <space>login<space><your_username>, and third row <space>password<space><your_password>')
                error = True
    except:
        print('Error reading client file. place it in ~/.netrc by eg. "cd", "nano .netrc". For more info, read the docs. ')
        error = True
        
        
        
        
    # Check there are no errors dates.
    start = args.get('start')
    end = args.get('end')
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        print(f"Error: Start date '{start}' is not a valid date.")
        error = True

    try:
        end_date = datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        print(f"Error: End date '{end}' is not a valid date.")
        error = True

    if 'start_date' in locals() and 'start_date' in locals():
        if start_date >= end_date:
            print(f"Error: Start date '{start}' is not before end date '{end}'.")
            error = True
        
        
        
        
        
        
    # Check if season is correct
    season = args.get('season')
    
    if season != 'none':
        try:
            start,end = season.strip().split(',')
            print(start,end)
            if start > 364 or end > 365 or start > end:
                print('Season values incorrect. Check that they are in DOY, less than 365, and that start is smaller than end.')
                error = True
        except ValueError:
            print('Ensure that seasons are separated by a comma.')
            error = True
    
    
    # Check that beam mode is correct.
    beamMode = args.get('beamMode')
    modes = ['EW', 'IW', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'WV']
    if beamMode not in modes:
        print(f'Error in beam mode ({beamMode}). Acceptable are: EW, IW, S1, S2, S3, S4, S5, S6, WV.')
        error = True
            
    # Check that flight direction is correct
    flightDirection = args.get('flightDirection')
    directions = ['ASCENDING','DESCENDING','ASC','DESC','A','D']
    
    if flightDirection not in directions:
        print('Faulty flight direction.')
        error = True
        
        
    # Check that polarization is correct
    target_pols = ['VV', 'VV+VH', 'Dual VV', 'VV+VH', 'Dual HV', 'Dual HH', 'HH', 'HH+HV', 'VV', 'Dual VH']
    try:
        pols = args.get('polarization').strip().split(',')
        for pol in pols:
            if pol not in target_pols:
                print(f'Error: Pol {pol} is incorrect. Acceptable polarizations are: VV, VV+VH, Dual VV, VV+VH, Dual HV, Dual HH, HH, HH+HV, VV, Dual VH.')
                error = True
        
    except ValueError:
        print('Make sure that pols are separated by a comma.')
        error = True
    
    
    # Check that processing level is correct
    processingLevel = args.get('processingLevel')
    levels = ['GRD_HS', 'GRD_HD', 'GRD_MS', 'GRD_MD', 'GRD_FD', 'SLC']
    
    if processingLevel not in levels:
        print(f'Incorrect processing level ({processingLevel}). Acceptable processing leves are: GRD_HS, GRD_HD, GRD_MS, GRD_MD, GRD_FD, SLC.')
        error = True
    
    
    # Make sure that processing values are boolean
    
    def to_bool(value):
        if isinstance(value, str):
            if value.lower() in ('true', '1'):
                return True
            elif value.lower() in ('false', '0'):
                return False
        return value
    
    slcSplit = args.get('slcSplit')
    applyOrbitFile = args.get('applyOrbitFile')
    thermalNoiseRemoval = args.get('thermalNoiseRemoval')
    calibration = args.get('calibration')
    slcDeburst = args.get('slcDeburst')
    speckleFiltering = args.get('speckleFiltering')
    polarimetricSpeckleFiltering = args.get('polarimetricSpeckleFiltering')
    terrainCorrection = args.get('terrainCorrection')
    bandMaths = args.get('bandMaths')
    linearToDb = args.get('linearToDb')
    args_list = [slcSplit, applyOrbitFile, thermalNoiseRemoval, calibration, slcDeburst, speckleFiltering, polarimetricSpeckleFiltering, terrainCorrection, bandMaths, linearToDb]
    args_names = ['slcSplit', 'applyOrbitFile', 'thermalNoiseRemoval', 'calibration', 'slcDeburst', 'speckleFiltering', 'polarimetricSpeckleFiltering', 'terrainCorrection', 'bandMaths', 'linearToDb']
    
    for arg, arg_name in zip(args_list, args_names):
        arg = to_bool(arg)
        if not isinstance(arg, bool):
            print(f'{arg_name} not boolean ({arg}). Set it to either True or False.')
            error = True
    
    
    # Check filter value
    try:
        filterResolution = int(args.get('filterResolution'))
    except ValueError:
        print(f'Error: filterResolution not an integer.')
        error = True
        
    # Check terrain value
    try: 
        terrainResolution = float(args.get('terrainResolution'))
    except ValueError:
        print('Error: terrainResolution not a float value.')
        error = True
    
                 
        
        
    
   
    # Check that processing matches the download processing parameter:
    process = args.get('process')
    if processingLevel == 'GRD_HD':
        grdprocesses = ['GRD','False']
        if process not in grdprocesses:
            print(f'Processing preset ({process}) does not match the download processing parameter ({processingLevel}).')
            error = True
                        
    elif processingLevel == 'SLC':
        slcprocesses = ['SLC','polSAR','False']
        if process not in slcprocesses:
            print(f'Processing preset ({process}) does not match the download processing parameter ({processingLevel}).')
            error = True
    
    
    # Terminate script
    if error:
        print('Terminating process. Check the parameters and run again.')
        parent_pid = os.getppid()
        os.kill(parent_pid, signal.SIGTERM)
        sys.exit(1)
        
    return args

        
def download_bulk_weather(source_path, result_path):
    """
    Caller function to bulk weather data download.
   
    """
    
    # Construct the command to run SarPipeline.py with the specified arguments
    command = [
        'python3', 'download_weather.py', source_path, result_path]
    
    # Run the command using subprocess
    subprocess.run(command)
    
    
def main():
    
    args = check_processing_parameters()
    
    # Get input arguments
    source_path = sys.argv[1]
    result_path = sys.argv[2]
    separate = sys.argv[3].lower() == 'true'
    bulkDownload = sys.argv[4].lower() == 'true'
    identifierColumn = args.get('identifierColumn')

    # Process input
    if source_path.endswith('.csv'):
        process_coordinates(source_path, result_path, bulkDownload)
        print("Coordinate processing complete.")
    else:
        process_shapefiles(source_path, result_path, identifierColumn, separate, bulkDownload)
        print("Shapefile processing complete. \n")
    folder_slurm = os.path.join(result_path, 'SLURM')
    folder_error = os.path.join(result_path, 'Error')
    os.makedirs(folder_slurm, exist_ok=True)
    os.makedirs(folder_error, exist_ok=True)
    
    if args.get('downloadWeather') == 'True':
        download_bulk_weather(source_path, result_path)
    
    
    
if __name__ == "__main__":
    main()