import os
import rasterio
import subprocess
import shutil
import numpy as np
from scipy.stats import norm, skew, kurtosis
from scipy.misc import derivative
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
#from datetime import datetime
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
import pandas as pd
import gc
import rioxarray
import xarray as xr
import csv
import sys
import datetime

try:
    from fmiopendata.wfs import download_stored_query
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "fmiopendata"])
    from fmiopendata.wfs import download_stored_query

from sklearn.preprocessing import MinMaxScaler

try:
    from pyinterpolate.idw import inverse_distance_weighting
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyinterpolate"])
    from pyinterpolate.idw import inverse_distance_weighting


from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from rasterio.enums import Resampling
import matplotlib.pyplot as plt
from scipy.stats import zscore
    
    

def read_arguments_from_file(file_path):
    """
    Extract arguments from the given text file.
    
    Input:
    - filePath (str): Full file path to the the text file.
    
    Output: 
    arguments (dict): Dictionary containing all the arguments within the text file.
    """
    arguments = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.strip().startswith('#'):
                arg_name, arg_value = line.strip().split('\t')
                arguments[arg_name.strip()] = arg_value.strip()
    return arguments    




###############

#METEOROLOGICAL FUNCTIONS

###############





def create_gdf(start_time, xmin, ymin, xmax, ymax):
    '''
    Function for creating the gdf with name, location, temp, and snow data.
    
    Input:
    Start_time
    
    Output:
    Geodataframe with columns 'Name', 'geometry', 'snow', and 'temperature' data.
    ''' 
    # Initialize dictionaries to store highest values for each location
    max_values = {
        'name': {},
        'temperature': {},
        'snow_depth': {},
        'precipitation_amount': {},
        'precipitation_intensity': {},
        'geometry': {}
    }
    
    # Initialize lists to store extracted values
    name_list = []
    geometry_list = []
    temperature_list = []
    snow_depth_list = []
    precipitation_amount_list = []
    precipitation_intensity_list = []
    
    # Download the data
    obs = download_weather_data(start_time, xmin, ymin, xmax, ymax)
    
    # Start loop to go through all dates
    for datetime_key, locations_data in obs.data.items():
        for location, weather_data in locations_data.items():

            # Extract and save name
            if location not in max_values['name']:
                max_values['name'][location] = True
                name_list.append(location)
                #print(location)

            # Extract and save temperature
            temperature_value = weather_data.get('Air temperature', {}).get('value')
            if location not in max_values['temperature']:
                max_values['temperature'][location] = []  # Create an empty list if it doesn't exist
            max_values['temperature'][location].append(temperature_value)  # Append the value to the list

            # Extract and save snow depth
            snow_depth_value = weather_data.get('Snow depth', {}).get('value')
            if location not in max_values['snow_depth']:
                max_values['snow_depth'][location] = []  # Create an empty list if it doesn't exist
            max_values['snow_depth'][location].append(snow_depth_value)  # Append the value to the list

            # Extract and save snow depth
            precipitation_amount_value = weather_data.get('Precipitation amount', {}).get('value')
            if location not in max_values['precipitation_amount']:
                max_values['precipitation_amount'][location] = []  # Create an empty list if it doesn't exist
            max_values['precipitation_amount'][location].append(precipitation_amount_value)  # Append the value to the list

                
            # Extract and save snow depth
            precipitation_intensity_value = weather_data.get('Precipitation intensity', {}).get('value')
            if location not in max_values['precipitation_intensity']:
                max_values['precipitation_intensity'][location] = []  # Create an empty list if it doesn't exist
            max_values['precipitation_intensity'][location].append(precipitation_intensity_value)  # Append the value to the list

                
                

            # Extract and save geometry
            location_metadata = obs.location_metadata.get(location, {})
            latitude = location_metadata.get('latitude')
            longitude = location_metadata.get('longitude')
            point = Point(longitude, latitude)
            if location not in max_values['geometry']:
                max_values['geometry'][location] = True
                geometry_list.append(point)
                
    
        # Calculate the mean for each variable and each location
    mean_values = {
        'temperature': {},
        'snow_depth': {},
        'precipitation_amount': {},
        'precipitation_intensity': {}
    }

    for variable in mean_values.keys():
        for location, values in max_values[variable].items():
            # Filter out NaN values
            valid_values = [value for value in values if not np.isnan(value)]
            if valid_values:  # Check if there are valid values for the location
                if variable == 'precipitation_amount':
                    mean_values[variable][location] = sum(valid_values)
                else:
                    mean_values[variable][location] = sum(valid_values) / len(valid_values)
            else:
                mean_values[variable][location] = None  # Handle case where there are no valid values

    # Print mean values
    #for variable, locations in mean_values.items():
    #    print(f"Mean {variable}:")
    #    for location, mean_value in locations.items():
    #        print(f"{location}: {mean_value}")

    # Convert dictionary values to lists
    name_list = list(max_values['name'].keys())
    #geometry_list = list(max_values['geometry'].keys())
    temperature_list = [mean_values['temperature'][location] for location in name_list]
    snow_depth_list = [mean_values['snow_depth'][location] for location in name_list]
    precipitation_amount_list = [mean_values['precipitation_amount'][location] for location in name_list]
    precipitation_intensity_list = [mean_values['precipitation_intensity'][location] for location in name_list]

    # Create a DataFrame
    data = {
        'Name': name_list,
        'geometry': geometry_list,
        'temperature': temperature_list,
        'snow': snow_depth_list,
        'precipitation amount': precipitation_amount_list,
        'precipitation intensity': precipitation_intensity_list
    }
    df = pd.DataFrame(data)

    # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Display GeoDataFrame
    #print(gdf)

    # Define the CRS
    gdf = gdf.set_crs(epsg=4326, inplace=True)
    gdf = gdf.to_crs(epsg=3067)
    
    return gdf

def download_weather_data(start_time, xmin, ymin, xmax, ymax):
    '''
    Function for downloading weather data from fmiopendata.
    
    Input:
    Start_time, in dt.datetime(yyyy,mm,dd) format.
    
    The end time is automatically 24 hours from this start time, i.e. a full day.
    
    
    Output:
    obs weather data, with obs.data giving the data, and obs.location_metadata giving geometries.
    '''    
    #import datetime as dt
    # Ensure proper formatting
    start_time_str = start_time.isoformat(timespec="seconds") + "Z"
    end_time = (start_time + datetime.timedelta(hours=23, minutes=59)).isoformat(timespec="seconds") + "Z"

    # Download data for the specified time range and bounding box, minx,miny,maxx,maxy
    obs = download_stored_query("fmi::observations::weather::multipointcoverage",
                                args=[f'bbox={xmin}, {ymin}, {xmax}, {ymax}',
                                      "starttime=" + start_time_str,
                                      "endtime=" + end_time,
                                      "timeseries=true"])
    
    
    return obs



  
    
def create_empty_grid():
    '''
    This function creates an empty grid based on a specified shapefile.

    Input:
    - shapefile_path: Path to the shapefile for the region of interest.

    Output:
    - The empty grid for the specified region.
    '''
    # Use roughly the reindeer herding area
    finland_fp = "/scratch/project_2001106/S1_reflectors/finland_shapefile/fi_10km.shp"
    finland_shp = gpd.read_file(finland_fp)
    finland_shp = finland_shp.to_crs('epsg:3067')

    # Extract the bounds of the MultiPolygon
    xmin, ymin, xmax, ymax = finland_shp.total_bounds

    # Specify the grid dimensions or cell size
    rows = 150
    cols = 50

    # Create a grid of points within the bounding box
    x = np.linspace(xmin, xmax, cols)
    y = np.linspace(ymin, ymax, rows)

    # Create a meshgrid from the x and y points
    xx, yy = np.meshgrid(x, y)

    # Create a list of Polygon geometries from the meshgrid
    polygons = [Polygon([(x, y), (x + (xmax - xmin) / cols, y), (x + (xmax - xmin) / cols, y + (ymax - ymin) / rows), (x, y + (ymax - ymin) / rows)]) for x, y in zip(xx.flatten(), yy.flatten())]

    # Create a GeoDataFrame from the list of Polygons
    gdf_grid = gpd.GeoDataFrame(geometry=polygons, crs=finland_shp.crs)

    # Clip the grid to the original MultiPolygon
    gdf_grid_clipped = gpd.clip(gdf_grid, finland_shp)

    return gdf_grid_clipped



def interpolate_grid(known_locations_gdf, 
                    unknown_locations_gdf, 
                    ):
    
    
    """
    This function should populate the grid based on the input data. This would be called twice, once for temp, once for snow.

    A helper function to do IDW interpolation for locations defined in 'unknown_points_gdf'.
    The values in column `value_column' of the 'known_points_gdf' are used as the basis for doing the interpolation.
    
    Parameters
    ----------
    
    known_locations_gdf : gpd.GeoDataFrame
        
        GeoDataFrame containing the known values at given points that are used as the basis for the interpolation.
        The geometries can be either points or polygons (a centroid of Polygon will be extracted). 
        
    unknown_locations_gdf : gpd.GeoDataFrame
        
        GeoDataFrame containing the unknown locations. The geometries can be either points or 
        polygons (a centroid of Polygon will be extracted). The values for these locations will be predicted using the 
        Inverse Distance Weighting interpolation method. 
        
    n_neighbors : int
        
        Number of neighbors to use for weighting. By default, all neighbors are used in the prediction (i.e. value: -1)
        
    power : int
    
        The power (𝛽) that defines the distance decay function (by default: 2). Higher power value emphasize the influence of the 
        points nearest to the unknown point. A smaller power value gives more equal influence of also more distant points.
        
    """
    
    
    # Parse the pointset for the known locations (training dataset)
    known_points_temp = get_pointset_for_interpolation(known_locations_gdf, 'temperature')
    known_points_snow = get_pointset_for_interpolation(known_locations_gdf, 'snow')
    known_points_pre_amount = get_pointset_for_interpolation(known_locations_gdf, 'precipitation amount')
    known_points_pre_intensity = get_pointset_for_interpolation(known_locations_gdf, 'precipitation intensity')

    #Create columns for predicted snow and temperature
    unknown_locations_gdf['predicted_temp'] = None
    unknown_locations_gdf['predicted_snow'] = None
    unknown_locations_gdf['predicted_pre_amount'] = None
    unknown_locations_gdf['predicted_pre_intensity'] = None

    # Interpolate the values with the test dataset
    for row in unknown_locations_gdf.itertuples():
        index = row.Index
        point = np.array([row.geometry.centroid.x, row.geometry.centroid.y])
        # Do the prediction using IDW
        valid_known_points_temp = known_points_temp[~np.isnan(known_points_temp[:, 2])]
        prediction_temp = inverse_distance_weighting(valid_known_points_temp, 
                                                point, 
                                                number_of_neighbours=-1, 
                                                power=2)
        # Assign the value to the result
        unknown_locations_gdf.loc[index, 'predicted_temp'] = round(prediction_temp, 4)

        # Do the prediction using IDW
        # Filter out NaN values from the known points
        valid_known_points_snow = known_points_snow[~np.isnan(known_points_snow[:, 2])]

        prediction_snow = inverse_distance_weighting(valid_known_points_snow, 
                                                point, 
                                                number_of_neighbours=-1, 
                                                power=2)
        # Assign the value to the result
        unknown_locations_gdf.loc[index, 'predicted_snow'] = round(prediction_snow, 4)
        
        
        
        # Do the prediction using IDW
        # Filter out NaN values from the known points
        valid_known_points_pre_amount = known_points_pre_amount[~np.isnan(known_points_pre_amount[:, 2])]

        prediction_pre_amount = inverse_distance_weighting(valid_known_points_pre_amount, 
                                                point, 
                                                number_of_neighbours=-1, 
                                                power=2)
        # Assign the value to the result
        unknown_locations_gdf.loc[index, 'predicted_pre_amount'] = round(prediction_pre_amount, 4)
        
        
        
        # Do the prediction using IDW
        # Filter out NaN values from the known points
        valid_known_points_pre_intensity = known_points_pre_intensity[~np.isnan(known_points_pre_intensity[:, 2])]

        prediction_pre_intensity = inverse_distance_weighting(valid_known_points_pre_intensity, 
                                                point, 
                                                number_of_neighbours=-1, 
                                                power=2)
        # Assign the value to the result
        unknown_locations_gdf.loc[index, 'predicted_pre_intensity'] = round(prediction_pre_intensity, 4)
        
    return unknown_locations_gdf




def get_pointset_for_interpolation(gdf, value_column):
    """
    A helper function to extract a pointset (numpy arrays) for interpolation. 
    
    Parameters
    ----------
    
    gdf: gpd.GeoDataFrame 
        
        Input GeoDataFrame from which the pointset for interpolation are parsed. The x and y coordinates
        are parsed from the geometry, and the z values are parsed from the selected column.
        In case the input geometries are polygons, a centroid of the given geometry is returned.
        
    value_column : str
        
        The name of the column that contains the values (z) for the attribute of interest 
        (e.g. the amount of copper observed at given location). 
    """
    
    # Extract x, y coordinates and the attribute (z) values from the gdf 
    x = gdf.geometry.centroid.x.values
    y = gdf.geometry.centroid.y.values
    z = gdf[value_column].values
    return np.array([x, y, z]).T


def find_meteorological_data(path, shapefile_path, start_date, end_date):

    dates = []
    grids = []
    temperatures = []
    snows = []
    precipitation_amounts = []
    precipitation_intensities = []

    
    
    xmin, ymin, xmax, ymax = find_bounds(shapefile_path)
    
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    dates = pd.date_range(start=start_date, end=end_date)
    i = 1
    for date in dates:
        gdf = create_gdf(date, xmin, ymin, xmax, ymax)

        #create grid for variables
        grid = create_empty_grid()
        grid = interpolate_grid(gdf, grid)
        grids.append(grid)
        print(f'{date.strftime("%d.%m.%Y")} ({i}/{len(dates)}) processed.', end='\r')
        i +=1
        
    print('\nAll meteorological data processed.')
    dates = [date.strftime('%Y-%m-%d') for date in dates]
    
    if not grids or not all('geometry' in grid for grid in grids):
        raise AttributeError('Grids do not contain geometry attribute.')

    # Extract variables and geometries from grids
    temperatures = [grid['predicted_temp'].values for grid in grids]
    snows = [grid['predicted_snow'].values for grid in grids]
    precipitation_amounts = [grid['predicted_pre_amount'].values for grid in grids]
    precipitation_intensities = [grid['predicted_pre_intensity'].values for grid in grids]
    geometries = grids[0]['geometry'].values

    # Convert geometries to WKT format for storage in xarray
    geometries_wkt = [geom.wkt for geom in geometries]

    # Create xarray Dataset
    ds = xr.Dataset(
        {
            "temperature": (["time", "geometry"], temperatures),
            "snow": (["time", "geometry"], snows),
            "precipitation_amount": (["time", "geometry"], precipitation_amounts),
            "precipitation_intensity": (["time", "geometry"], precipitation_intensities),
        },
        coords={
            "time": pd.to_datetime(dates),
            "geometry": geometries_wkt
        }
    )

    # Save to NetCDF
    ds.to_netcdf(os.path.join(path,'weather.nc'))
    
def find_bounds(pathToShapefile):
    gdf = gpd.read_file(pathToShapefile)
    crs = gdf.crs
    
    #change to 3067 to create a 500m buffer
    if crs != 'epsg:4326':
        gdf = gdf.to_crs(epsg=4326)
        crs = 'epsg:4326'
        
    # Calculate the outer bounds of all polygons    
    bounds = gdf.geometry.bounds
    
    xmin = gdf.geometry.bounds['minx'].iloc[0] - 1
    ymin = gdf.geometry.bounds['miny'].iloc[0] - 1
    xmax = gdf.geometry.bounds['maxx'].iloc[0] + 1
    ymax = gdf.geometry.bounds['maxy'].iloc[0] + 1
    
    return xmin, ymin, xmax, ymax


def main():
    print('Downloading weather data...')
    args = read_arguments_from_file(os.path.join(os.getcwd(), 'arguments.txt'))
    timeseries = args.get('timeseries') == 'True'
    movingAverage = args.get('movingAverage') == 'True'
    movingAverageWindow = int(args.get('movingAverageWindow'))
    start = args.get('start')
    end = args.get('end')
    
    if timeseries:
        source_path = sys.argv[1]
        path = sys.argv[2]
        find_meteorological_data(path, source_path, start, end)
        print('Weather data downloaded.')
        
    else:
        print('Timeseries not done.')
            
    
        ds = xr.Dataset(
        {'temperature': (('date', 'geometry'), grid['predicted_temp'].values)},
        {'snow': (('date', 'geometry'), grid['predicted_snow'].values)},
        {'precipitation_amount': (('date', 'geometry'), grid[grid['predicted_pre_amount']].values)},
        {'precipitation_intensity': (('date', 'geometry'), grid[grid['predicted_pre_intensity']].values)},
        coords={
            'date': dates,
            'geometry': grid['geometry']
                }
            )


if __name__ == "__main__":
    main()