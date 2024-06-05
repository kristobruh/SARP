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
from shapely import wkt
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
    
    

def parse_file_info(data_path):
    '''
    Parse file name and date from the processed tiffs, and sort by date. Not 100% necessary anymore, but some of the older code I wrote utilize this so it remains.
    
    Inputs:
    - data_path (str): Full path to the folder which contains the tiff files.
    
    Output:
    - df (pd.dataFrame): A dataframe containing columns for times and names of the files.
    '''
    # Create a DataFrame to store VV and VH values along with time
    df = pd.DataFrame(columns=['TIME', 'name'])
    
    # Get list of GeoTIFF files
    tiff_files = [file for file in os.listdir(data_path) if file.endswith('.tif')]
    
    i = len(tiff_files)
    
    # Loop over each GeoTIFF file
    for tiff_file in tiff_files:
        # Parse time from filename
        time = os.path.splitext(tiff_file)[0].split('_')[-2]
        # Convert time to datetime format
        time = pd.to_datetime(time, format='%Y%m%d')
        
        # Add the time and full filename to the DataFrame
        df = pd.concat([df, pd.DataFrame({'TIME': [time], 'name': [tiff_file]})], ignore_index=True)

        i -= 1
        
    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
    df = df.sort_values(by='TIME')
    df = df.reset_index(drop=True)
    
    return df



def resize_raster(data, shape):
    '''
    A legacy method of resizing a raster so that raster averaging can be done. Another function using a different method is down below for xarrays, but for now this works for the tiffs.
    
    Inputs:
    - data (array): A raster to be resized.
    - shape (array): a 2-vaue array describing the x-y shape to which the raster will be resized.
    
    Output:
    - new_data (array): 
    '''
    new_data = np.zeros((data.shape[0], shape[1], shape[2]))
    min_height = min(data.shape[1], shape[1])
    min_width = min(data.shape[2], shape[2])
    new_data[:, :min_height, :min_width] = data[:, :min_height, :min_width]
    return new_data

def calculate_average_raster(df, data_path, output_folder, window):
    '''
    Calculates a moving average of a defined window size for the processed rasters.
    
    Inputs:
    - df (pd.dataFrame): A dataframe containing columns for times and names of the files.
    - data_path (str): Full path to the folder where the processed tiff are located.
    - output_folder (str): Full path to the folder to be created and where the averaged raster are saved.
    - window (int): Number of observations to be included in the moving average. An even value is recommended.
    
    Output:
    - Folder masked_tiffs that contains all the averaged rasters.
    '''
    
    # Create the output folder
    os.makedirs(output_folder, exist_ok=True)
    
    for i in range(window, len(df)):
        # Get the current file and the three previous files
        current_file = df.iloc[i]['name']
        previous_files = df.iloc[i-(window-1):i]['name'].tolist()
        
        # Open the current file
        with rasterio.open(os.path.join(data_path, current_file)) as src_current:
            # Read the data from the current file
            data_current = src_current.read()
            # Copy the metadata from the current file
            profile = src_current.profile
            # Add the pixel values from the current file to the cumulative sum
            sum_data = data_current
        
        # Loop through the previous files
        for previous_file in previous_files:
            with rasterio.open(os.path.join(data_path, previous_file)) as src_previous:
                # Read the data from the previous file
                data_previous = src_previous.read()
                # Resize previous raster if shapes are different
                if data_previous.shape != data_current.shape:
                    # Resize previous raster if shapes are different
                    if data_previous.shape != data_current.shape:
                        data_previous = resize_raster(data_previous, data_current.shape)

                # Add the pixel values to the cumulative sum
                sum_data += data_previous
       
            
        # Calculate the average pixel values
        average_data = sum_data / window

        # Create the output file path
        output_file = os.path.join(output_folder, f'{current_file[:-4]}_averaged.tif')

        # Write the average data to a new raster file
        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(average_data)
            
            

def mask_and_save_rasters(data_path, path_to_shapefile, output_folder):
    '''
    Calculates a moving average of a defined window sizwe for the processed rasters.
    
    Inputs:
    - data_path (str): Full path to the folder where the processed tiff are located.
    - path_to_shapefile (str): Full path to the shapefile to which masking is done.
    - output_folder (str): Full path to the folder to be created and where the averaged raster are saved.
    
    Output:
    - Folder masked_tiffs that contains all the masked rasters. Averaged non-masked rasters are deleted for brevity.
    '''
    
    os.makedirs(output_folder, exist_ok=True)

    shapefile = gpd.read_file(path_to_shapefile)
    # Change to 3067
    if shapefile.crs != 'epsg:3067':
        shapefile = shapefile.to_crs(epsg=3067)
    shapefile['geometry'] = shapefile.geometry.buffer(-20)
    # Get list of averaged raster files
    files = [file for file in os.listdir(data_path) if file.endswith('.tif')]
    
    # Loop over each raster file
    for file in files:
        # Open the averaged raster file
        with rasterio.open(os.path.join(data_path, file)) as src:
            # Mask the raster with the shapefile
            out_image, out_transform = mask(src, shapefile.geometry, crop=True, nodata=np.nan)
            
            # Create output filename
            output_tiff_file = os.path.splitext(file)[0] + '_masked.tif'
            output_path = os.path.join(output_folder, output_tiff_file)
            
           
            # ------- START FILTERING BAD IMAGES -------
            vh_band = out_image[0]
            vv_band = out_image[1]

            vv_mean = np.nanmean(vv_band)
            vh_mean = np.nanmean(vh_band)
            std = np.nanstd(vv_band)

            # Count NaN values
            nan_count = np.sum(np.isnan(vv_band))
            total_pixels = vv_band.size
            nan_percentage = nan_count / total_pixels

            # Count 0-values
            zero_count = np.sum(vv_band == 0.0)
            zero_percentage = zero_count / total_pixels

            # Count low values
            low_count = np.sum(vv_band < -49)
            low_percentage = low_count / total_pixels

            # Check filtering criteria
            if vv_mean == 0 or vh_mean == 0 or std > 15 or zero_percentage > 0.1 or low_percentage > 0.05:
                continue  # Skip to the next raster file if any criterion is met
                

            # ------- END FILTERING BAD IMAGS -------
            else:
                # Write the masked raster to a new GeoTIFF file
                with rasterio.open(
                    output_path,
                    'w',
                    driver='GTiff',
                    height=out_image.shape[1],
                    width=out_image.shape[2],
                    count=src.count,
                    dtype=out_image.dtype,
                    crs=src.crs,
                    transform=out_transform,
                ) as dst:
                    for i in range(1, src.count + 1):
                        dst.write(out_image[i - 1], i)
            

            # Delete the original unmasked file
            #os.remove(os.path.join(output_folder, averaged_file))      

            
def calculate_inflection(data):
    '''
    Calculates the second inflection point of a normal distribution fitted to a data array.
    
    Inputs:
    - data (raster): A raster to which the operation is performed.
    
    Output:
    - x[idx_max_dy] (float): VV-value of the inflection point.
    '''
    # Fit a normal distribution to the data (excluding NaN values)
    mu = np.nanmean(data)
    std = np.nanstd(data)
    # Generate x-values for the normal distribution
    x = np.linspace(np.nanmin(data), np.nanmax(data), 100)

    # Calculate the corresponding y-values for the normal distribution
    y = norm.pdf(x, mu, std)

    # Calculate the minimum of the first derivative (normal curve second inflection point)
    dy = np.diff(y)
    idx_max_dy = np.argmin(dy)

    return x[idx_max_dy]


def calculate_ice(masked_path,ice_path):
    '''
    Creates ice threshold rasters based on the averaged summer water Sigma0 values. The threshold is determined as the average inflection point of the summer normal distributions. The idea is that the threshold is where most of the water values are omitted, and as ice and snow starts to form, the intensities move to the right and thus ice formation is observed.
    
    Inputs:
    - masked_path (str): Full path to the folder where the masked rasters are located.
    - ice_path (str): Full path to the folder where the ice rasters are saved.
    
    Output:
    - threshold_list (list): A list of threshold values for each date, used for plotting purposes if needed.
    '''
    # Create output folder
    output_folder = ice_path
    os.makedirs(output_folder, exist_ok=True)
    
    # Get list of files in the folder
    input_folder = masked_path
    files = [file for file in os.listdir(input_folder) if file.endswith('.tif')]
    files = sorted(files, key=lambda x: x.split('_')[-4])
    
    # Initialize placeholder threshold and year
    threshold = -18
    current_year = 2018
    inflection_sum = 0
    no_of_inflections = 0
    threshold_list = []
    reset_inflection = True
    
    # Iterate over each file
    for file in files:
        input_file_path = os.path.join(input_folder, file)
        output_file_path = os.path.join(output_folder, file[:-4]+'_ice.tif')
        
        # Extract year and month data
        parts = file.split('_')
        date_str = parts[-4]
        year = int(date_str[:4])
        month = int(date_str[4:6])
        
        # Open the input raster file
        with rasterio.open(input_file_path, 'r') as src:
            # Read the raster data
            data = src.read()
            profile = src.profile
            
            # If we hit a new summer, the inflection calculation is reset
            if year > current_year and month == 7 and reset_inflection:
                current_year = year
                inflection_sum = 0
                no_of_inflections = 0
                reset_inflection = False
            
            # For the current year, all observations from the summer are saved
            if year == current_year and 7 <= month <= 10:
                # Calculate inflection point, save
                inflection_sum += calculate_inflection(data[1])
                # Calculate number of saves
                no_of_inflections += 1
                
            # Once summer passes, calculate new threshold:
            if year == current_year and month > 10:
                threshold = inflection_sum / no_of_inflections
                reset_inflection = True
                
            # Apply the linear scaling to the second band
            ice_band = np.interp(data[1], [threshold - 0.7, threshold + 0.7], [0, 1])
            ice_band[data[1] < threshold - 0.7] = 0
            #ice_band[np.isnan(data[1])] = 0
            ice_band[data[1] > threshold + 0.7] = 1
            # Save the threshold to a list for plotting purposes
            threshold_list.append(threshold)
            
            # Create a new raster file with only the ice band
            profile['count'] = 1  # Set the number of bands
            profile['dtype'] = 'float32'  # Set the data type
            
            with rasterio.open(output_file_path, 'w', **profile) as dst:
                dst.write(ice_band.astype('float32'), 1)  # Write the ice band
            
    return threshold_list
    
def extract_ice(ice_path):
    '''
    Extracts the data from the ice rasters to a list of arrays.
    
    Inputs:
    - ice_path (str): Full path to the folder where the ice rasters are.
    
    Output:
    - ice_bands (list): A list containing all the ice raster arrays.
    - dates (list): A list of dates corresponding to the arrays.
    - means (list): A list of the mean ice values, as a fraction of how much is covered in ice.
    '''
    # Get list of TIFF filenames
    tiff_files = [file for file in os.listdir(ice_path) if file.endswith('.tif')]
    
    # Sort filenames based on the date element
    tiff_files.sort(key=lambda x: x.split('_')[-5])
    
    ice_bands = []
    dates = []
    means = []
    
    # Loop over each TIFF file
    i = len(tiff_files)
    for tiff_file in tiff_files:
        # Extract date from filename
        date_str = tiff_file.split('_')[-5]
        # Parse date string to datetime object
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        # Open the GeoTIFF file
        with rasterio.open(os.path.join(ice_path, tiff_file)) as src:
            # Read the ice band
            ice_band = src.read(1)
            
            # Store third band and date
            ice_bands.append(ice_band)
            dates.append(date)
            means.append(np.nanmean(ice_band))
            i -= 1
    return ice_bands, dates, means

def extract_VV(masked_path):
    '''
    Extracts the data from the masked rasters to a list of arrays.
    
    Inputs:
    - masked_path (str): Full path to the folder where the masked rasters are.
    
    Output:
    - VVs (list): A list containing all the VV raster arrays.
    - VHs (list): A list containing all the VH raster arrays.
    - dates (list): A list of dates corresponding to the arrays.
    '''
    from datetime import datetime
    # Get list of TIFF filenames
    tiff_files = [file for file in os.listdir(masked_path) if file.endswith('.tif')]
    
    # Sort filenames based on the date element
    tiff_files.sort(key=lambda x: x.split('_')[0])  # Date is the 5th element
    
    VVs = []
    VHs = []
    dates = []  # Store dates for annotation
    
    # Loop over each TIFF file
    i = len(tiff_files)
    for tiff_file in tiff_files:
        # Extract date from filename
        date_str = tiff_file.split('_')[0]
        # Parse date string to datetime object
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        # Open the GeoTIFF file
        with rasterio.open(os.path.join(masked_path, tiff_file)) as src:
            # Read band 2
            VV = src.read(2)
            VH = src.read(1)
            
            # Store VV and date
            VVs.append(VV)
            VHs.append(VH)
            dates.append(date)
            i -= 1
    
    return VVs, VHs, dates
    

def resize_to_smallest(bands):
    '''
    Resizes all the arrays to the smallest raster. This is done so that concatenation to xarray can be done accurately.
    
    Inputs:
    - bands (list): A list of arrays to be resized.
    
    Output:
    - bands (list): A list resized arrays.
    '''
    
    smallest = (99999999, 99999999)
    for i, sub_array in enumerate(bands):

        # Check if any dimension of the current sub-array is smaller than the corresponding dimension of previous
        if np.any(np.array(sub_array.shape) < np.array(smallest)):
            # Update previous with the smaller dimension of the current sub-array
            smallest = tuple(min(prev_dim, cur_dim) for prev_dim, cur_dim in zip(smallest, sub_array.shape))
            #data_previous = resize_raster(data_previous, data_current.shape)

    # Iterate through all sub-arrays again and trim to match the smallest dimensions
    for i, sub_array in enumerate(bands):
        # Check if any dimension of the current sub-array is larger than the corresponding dimension of previous
        if np.any(np.array(sub_array.shape) > np.array(smallest)):

            # Calculate the slice indices to trim the sub-array
            slice_indices = tuple(slice(0, dim) for dim in smallest)

            # Trim the sub-array
            trimmed_sub_array = sub_array[slice_indices]

            # Update the sub-array with the trimmed version
            bands[i] = trimmed_sub_array
            
    return bands

def create_xarray(bands, dates, flip):
    '''
    Creates an xarray of the wanted bands.
    
    Inputs:
    - bands (list): A list of arrays to be converted.
    - dates (list): A list of dates corresponding to the arrays.
    - flip (boolean): Whether an array is fliiped horizontally.
    
    Output:
    - bands_ds (xarray): A xarray of the bands.
    '''
    # Create an empty list to store DataArrays
    data_arrays = []

    # Iterate through each sub-array and corresponding date
    for sub_array, date in zip(bands, dates):
        # Create a DataArray for the current sub-array
        if flip:
            sub_array = np.flip(sub_array, axis=0)
        data_array = xr.DataArray(sub_array, dims=('y', 'x'))

        # Assign the date as a coordinate
        data_array = data_array.assign_coords(time=date)

        # Append the DataArray to the list
        data_arrays.append(data_array)

    # Concatenate the list of DataArrays along the 'time' dimension to create an xarray Dataset
    bands_ds = xr.concat(data_arrays, dim='time')
    
    return bands_ds

def calculate_first_freeze(ice_fraction, dates):
    '''
    Creates the first day of proper freezing of a season based on defined criteria. Now they are that ice cover has to be over 40% for two consecutive observations.
    
    Inputs:
    - ice_fraction (list): A list of ice fraction over the lake.
    - dates (list): A list of dates corresponding to the ice fractions.
    
    Output:
    - freezing_date (list): A list of first freezing dates of all covered seasons.
    '''
    previous_frac = 0
    freezing_date = []
    cooldown = 0

    for date, fraction in zip(dates, ice_fraction):
        if cooldown > 0:
            cooldown -= 1
            continue

        month = (datetime.strptime(date, '%Y-%m-%d')).month
        year = (datetime.strptime(date, '%Y-%m-%d')).year
        if month > 10 or month < 3:
            if fraction > 0.5 and previous_frac > 0.5:
                freezing_date.append(previous_date)
                cooldown = 20

            previous_frac = fraction
            previous_date = date

    return freezing_date

def calculate_statistics(VV, VH, dates, output_path):
    '''
    Calculates statistics for all bands and saves them to a csv.
    
    Inputs:
    - VV (list): A list containing all the VV raster arrays.
    - VH (list): A list containing all the VH raster arrays.
    - dates (list): A list of dates corresponding to the arrays.
    - output_path (list): Full path to the folder where the csv will be saved.
    
    Output:
    - A saved csv.
    '''
    
    # Initialize lists to store statistics for each band
    VV_mean = []
    VV_min = []
    VV_max = []
    VV_std = []
    VH_mean = []
    VH_min = []
    VH_max = []
    VH_std = []

    # Iterate over each date
    for vv_band, vh_band in zip(VV, VH):
        # Calculate statistics for VV band
        vv_mean = np.nanmean(vv_band)
        vv_min = np.nanmin(vv_band)
        vv_max = np.nanmax(vv_band)
        vv_std = np.nanstd(vv_band)
        
        # Calculate statistics for VH band
        vh_mean = np.nanmean(vh_band)
        vh_min = np.nanmin(vh_band)
        vh_max = np.nanmax(vh_band)
        vh_std = np.nanstd(vh_band)
        
        # Append statistics to lists
        VV_mean.append(vv_mean)
        VV_min.append(vv_min)
        VV_max.append(vv_max)
        VV_std.append(vv_std)
        VH_mean.append(vh_mean)
        VH_min.append(vh_min)
        VH_max.append(vh_max)
        VH_std.append(vh_std)

    # Write statistics to CSV file
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerow(['Date', 'VV Mean', 'VV Min', 'VV Max', 'VV Std', 'VH Mean', 'VH Min', 'VH Max', 'VH Std'])
        for date, vv_mean, vv_min, vv_max, vv_std, vh_mean, vh_min, vh_max, vh_std in zip(dates, VV_mean, VV_min, VV_max, VV_std, VH_mean, VH_min, VH_max, VH_std):
            writer.writerow([date, vv_mean, vv_min, vv_max, vv_std, vh_mean, vh_min, vh_max, vh_std])
            
            
from sklearn.preprocessing import MinMaxScaler

try:
    from pyinterpolate.idw import inverse_distance_weighting
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyinterpolate"])
    from pyinterpolate.idw import inverse_distance_weighting


from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

import rasterio
from rasterio.enums import Resampling
import os
import datetime
import matplotlib.pyplot as plt
from scipy.stats import zscore


def find_reflector(path, upscale_factor):
    '''
    Finds reflector location based on the last 20 observations. Needs images which are roughly centered on the reflector, 
    with a maximum offset of 100m to any side. This offset can be increased in find_coarse, but the risk of including 
    false positives such as buildings increase. More observations can be used if necessary, but you should try to avoid 
    wintertime due to possible snow accumulation.
    
    You can adjust the finding parameters by increasing the search radius as described earlier, and by changing the 
    outlier sensitivity in filter_outliers. If you need to search for the reflector from afar, you might want to decrease
    the z-value threshold to 1 to remove potential outliers. You may also change upsampling paramters to see what gives 
    a good result.
    
    Input:
    path (str): Full path to the directory where a site's processed tiffs are located.
    
    Outputs:
    Currently lots, will be refined.
    '''
    
    
    # Initialize lists
    VV_means = []
    VH_means = []
    dates = []
    VV_max = []
    VH_max = []
    VV_arr = []
    max_indices = []
    
    # Sort data, use only the last 20 observations.
    files = sorted([f for f in os.listdir(path) if f.endswith('.tif')])[-20:]
    
    # Start going through each file
    for file in files:
        #print(file)
        # Ensure we're working with a tif
        if not file.endswith('.tif'):
            continue
            
        with rasterio.open(os.path.join(path,file)) as src:
            # Upsample data for more precise positioning
            data = src.read(
                out_shape=(
                    src.count,
                    int(src.height * upscale_factor),
                    int(src.width * upscale_factor)
                ),
                resampling=Resampling.bilinear
            )

            # Scale image transform
            transform = src.transform * src.transform.scale(
                (src.width / data.shape[-1]),
                (src.height / data.shape[-2])
            )
            
            # Read data to bands and remove 0.0 values
            VH_band = data[0]
            VH_band[VH_band == 0.0] = np.nan
            VV_band = data[1]
            rows, cols = VV_band.shape
            
            # Find the rough location in the center based on brightest pixel
            max_index = find_coarse(VV_band)
            row, col = max_index
            
            # Find the precise location based on neighborhood values
            #print(f'Starting row and col: {row}, {col}')
            neighbor_mean, row, col = find_fine(row,col,VV_band, end=False)
            #print(f'Final: {neighbor_mean}, {row}, {col} \n')
            max_index = (row,col)
            max_indices.append(max_index)
            max_value = VV_band[max_index]
            VH_max.append(VH_band[max_index])
            VV_means.append(neighbor_mean)
            VV_max.append(max_value)
            
            # Extract temporal data
            parts = file.split('_')
            date_str = parts[0]
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:])
            date = datetime.datetime(year, month, day)
            dates.append(date)
            
            #if VV_arr is None:
            #    VV_arr = np.zeros_like(VV_band)
            
            VV_arr.append(VV_band)
            
    # Create an averaged array for illustration purposes            
    VV_arr = resize_to_smallest(VV_arr)
    sum_VV = np.zeros_like(VV_arr[0])
    for arr in VV_arr:
        sum_VV =+ arr 
    avg_VV = sum_VV / len(sum_VV)
    
    # Filter outliers
    filtered_indices = filter_outliers(max_indices)
    rows, cols = zip(*max_indices)
    row = np.mean(rows)
    col = np.mean(cols)
    final_position = (round(row),round(col))
    
            
    return VV_max, VH_max, avg_VV, max_indices, filtered_indices, final_position


def find_coarse(raster):
    '''
    Finds a reflectors' rough location based on a simple highest highest pixel value within a given radius from the
    center pixel. Radius values are in pixel units, i.e. when upsampled from 10m to 1m, a radius of 100 searches 
    up to 100m away.
    
    Input:
    raster (np.array): Raster which is to be searched.
    
    Output:
    max_index (tuple): Index of the highest value pixel.
    '''
    
    radius = 100  # 5-pixel radius means a 5x5 window, centered around the given row and column
    max_value = -np.inf
    max_index = None

    rows, cols = raster.shape
    row = rows // 2
    col = cols // 2 
    
    for i in range(row - radius, row + radius + 1):
        for j in range(col - radius, col + radius + 1):
            # Check if the current indices are within the bounds of the raster
            if 0 <= i < raster.shape[0] and 0 <= j < raster.shape[1]:
                # Calculate the distance from the center pixel
                distance = np.sqrt((i - row)**2 + (j - col)**2)
                if distance <= radius:  # Check if the pixel is within the radius
                    # Update the maximum value and its index if a higher value is found
                    if raster[i, j] > max_value:
                        max_value = raster[i, j]
                        max_index = (i, j)

    return max_index


def find_fine(row, col, raster, end):
    '''
    Finds a reflectors' 'precise' location based on a recursive queen contiguity search. The basic steps are:
    
    1. Identify all queen contiguity neighbors from the pixel
    2. Call recursively all neighboring pixels as well and calculate their neighborhood means
    3. If any neighbor has a larger mean, switch to that pixel and repeat the process recursively
    
    Input:
    raster (np.array): Raster which is to be searched.
    row (int): Row number
    col (int): Column number
    end (boolean): Whether to continue the recursion to neighborhood pixels. Default is false.
    
    Output:
    mean (float): The final value.
    row_return: 
    '''
    #row_return = row
    #col_return = col
    # Define the directions of queen neighbors (including second order)
    directions = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
    
    # Initialize variables for calculating the mean
    neighbor_values = []
    dxs = []
    dys = []
    
    # Iterate over each direction, save values
    for dx, dy in directions:
        # Calculate the coordinates of the neighboring pixel
        neighbor_row = row + dx
        neighbor_col = col + dy
        
        # Add the value of the neighboring pixel to the list
        neighbor_values.append(raster[neighbor_row, neighbor_col])
        dxs.append(dx)
        dys.append(dy)
        #print(raster[neighbor_row, neighbor_col])

    # Calculate the mean of the neighboring pixel values
    mean = np.mean(neighbor_values)
    
    
    if end:
        return mean, row, col
    
    for dx, dy in directions:
        if dx == 0 and dy == 0:
            continue
        new_mean,_,_ = find_fine(row + dx, col + dy, raster, end=True)
        #print(f'Current: {mean}, new: {new_mean}')
        if new_mean > mean:
            #print('Found a larger neighbor, calling recursively...')
            #print(f'Found at {row+dx}, {col+dy}')
            mean = new_mean
            mean,row,col = find_fine(row + dx, col + dy, raster, end=False)
            #row = row + dx
            #col = col + dy

    return mean, row, col


def filter_outliers(indices):
    '''
    Compute 
    
    Input:
    raster (np.array): Raster which is to be searched.
    row (int): Row number
    col (int): Column number
    end (boolean): Whether to continue the recursion to neighborhood pixels. Default is false.
    
    Output:
    mean (float): The final value.
    row_return: 
    '''
    # Convert indices to separate arrays for rows and columns
    rows, cols = zip(*indices)

    # Calculate z-scores for rows and columns
    z_scores_rows = zscore(rows)
    z_scores_cols = zscore(cols)

    # Define threshold for z-score
    threshold = 2

    # Filter indices based on z-score threshold
    filtered_indices = [indices[i] for i in range(len(indices)) if abs(z_scores_rows[i]) <= threshold and abs(z_scores_cols[i]) <= threshold]
    
    return filtered_indices






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

def find_meteorological_data(data_path, path, target, pathToShapefile):
    
    
    #data_path = os.path.join(path,target,'tiffs')
    lat_weight = False
    temporal_weight = False
    files = sorted([f for f in os.listdir(data_path) if f.endswith('.tif')])
    dates = []
    temperatures = []
    snows = []
    precipitation_amounts = []
    precipitation_intensities = []

    
    
    xmin, ymin, xmax, ymax = find_bounds(pathToShapefile)

    print('Fetching meteorological data...')
    for file in files:
        # Extract temporal data
        parts = file.split('_')
        date_str = parts[0]
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:])
        date = datetime.datetime(year, month, day)
        dates.append(date)
        
    
    dates = pd.date_range(start=min(dates), end=max(dates))
    i = 1
    
    current_time = min(dates)
    for date in dates:
        
        gdf = create_gdf(date, xmin, ymin, xmax, ymax)

        #create grid for variables
        grid = create_empty_grid()
        grid = interpolate_grid(gdf, grid)

        # Find data
        shapefile = gpd.read_file(pathToShapefile)
        joined_gdf = gpd.sjoin(grid, shapefile, how='inner', predicate='intersects')

        # Extract the relevant columns to variables
        geometry = joined_gdf['geometry']
        #temperature = joined_gdf['predicted_temp'].values[0]
        #snow = joined_gdf['predicted_snow'].values[0]
        #precipitation_amount = joined_gdf['predicted_pre_amount'].values[0]
        #precipitation_intensity = joined_gdf['predicted_pre_intensity'].values[0]

        temperatures.append(joined_gdf['predicted_temp'].values[0])
        snows.append(joined_gdf['predicted_snow'].values[0])
        precipitation_amounts.append(joined_gdf['predicted_pre_amount'].values[0])
        precipitation_intensities.append(joined_gdf['predicted_pre_intensity'].values[0])

        print(f'{date.strftime("%d.%m.%Y")} ({i}/{len(dates)}) processed.', end='\r')
        i +=1
        
    print('\nAll meteorological data processed.')
    dates = [date.strftime('%Y-%m-%d') for date in dates]
    
    data = {
        'date': dates,
        'temperature': temperatures,
        'snow': snows,
        'precipitation_amount': precipitation_amounts,
        'precipitation_intensity': precipitation_intensities
    }

    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file
    df.to_csv(f'{path}/{target}/{target}_meteo.csv', index=False)
    
    return temperatures, snows, precipitation_amounts, precipitation_intensities, dates


def make_plot(path,target,temperature,precipitation_amount,snows,VV,VH,dates,meteo_dates, reflector):
    
    if not reflector:
        # find mean of each array
        VV_list = []
        VH_list = []
        for VV_arr, VH_arr in zip(VV, VH):
            VV_list.append(np.nanmean(VV_arr))
            VH_list.append(np.nanmean(VH_arr))
            
        VV = VV_list
        VH = VH_list
    
    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot VV and VH on the left axis
    line1, = ax1.plot(dates, VV, label='VV', color='blue', linewidth=2)
    line2, = ax1.plot(dates, VH, label='VH', color='green', linewidth=2)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('VV and VH', color='black')
    ax1.set_ylim(-70,10)

    # Create another y-axis for the right side
    ax2 = ax1.twinx()

    # Plot precipitation amount on the right axis
    line3, = ax2.plot(meteo_dates, precipitation_amount, label='Daily precipitation, mm', color='red')
    ax2.set_ylabel('Daily precipitation, mm', color='black')
    ax2.set_ylim(0,40)

    # Create a third y-axis for the right side
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))  # Adjust the position of the axis

    # Plot temperature on the right axis
    line4, = ax3.plot(meteo_dates, temperature, label='Temperature', color='orange')
    ax3.set_ylabel('Temperature', color='black')
    ax3.set_ylim(-30,30)
    ax3.axhline(0,linestyle='--',color='black',linewidth=0.5)

    ax4 = ax1.twinx()
    ax4.spines['right'].set_position(('outward', 120))  # Adjust the position of the axis
    line5, = ax4.plot(meteo_dates, snows, label='Snow depth', color='black')
    ax4.set_ylabel('Snow (cm)', color='black')
    ax4.set_ylim(0,100)

    # Combine legend for all lines
    lines = [line1, line2, line3, line4, line5]
    labels = [line.get_label() for line in lines]
    legend = ax2.legend(lines, labels, loc='lower left',framealpha=0.85)
    legend.set_zorder(10)

    ax1.tick_params(axis='x', rotation=45)
    ax1.set_xticks(dates[::4])
    ax1.set_xticklabels(dates[::4], rotation=45)

    plt.title(f'{target} and weather conditions, {min(dates)} - {max(dates)}')

    plt.savefig(f'{path}/{target}/{target}_weather.png', dpi=150, bbox_inches='tight')
    
    
def make_location_fig(path,target,max_indices,filtered_indices,VV_arr,position):
    plt.figure(figsize=(8, 8))
    plt.imshow(VV_arr, cmap='gray')
    plt.scatter([idx[1] for idx in max_indices], [idx[0] for idx in max_indices], color='red', marker='x', label='Outlier observation')
    plt.scatter([idx[1] for idx in filtered_indices], [idx[0] for idx in filtered_indices], color='yellow', marker='x', label='Inlier observation')
    plt.scatter(position[1],position[0], color='blue', marker='o',label='Final position')
    #plt.scatter(604,595, color='blue', marker='o')
    plt.title(f'Reflector location, {target}')
    #plt.xlim(550,650)
    #plt.ylim(550,650)
    plt.legend(loc='upper right')
    plt.xlabel('Column Index')
    plt.ylabel('Row Index')
    plt.savefig(f'{path}/{target}/{target}_location.png', dpi=150, bbox_inches='tight')
    plt.show()
    
def extract_VV_meteo(path, position, upscale_factor):
    '''
    Extracts the data from the masked rasters to a list of arrays.
    
    Inputs:
    - path (str): Full path to the folder where the rasters are.
    
    Output:
    - VVs (list): A list containing all the VV raster arrays.
    - VHs (list): A list containing all the VH raster arrays.
    - dates (list): A list of dates corresponding to the arrays.
    '''
    from datetime import datetime
    # Get list of TIFF filenames
    tiff_files = [file for file in os.listdir(path) if file.endswith('.tif')]
    
    # Sort filenames based on the date element
    tiff_files.sort(key=lambda x: x.split('_')[-2])
    
    VVs = []
    VHs = []
    dates = []  # Store dates for annotation
    
    # Loop over each TIFF file
    i = len(tiff_files)
    for tiff_file in tiff_files:
        # Extract date from filename
        date_str = tiff_file.split('_')[-2]
        # Parse date string to datetime object
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        # Open the GeoTIFF file
        with rasterio.open(os.path.join(path, tiff_file)) as src:
            
            data = src.read(
                out_shape=(
                    src.count,
                    int(src.height * upscale_factor),
                    int(src.width * upscale_factor)
                ),
                resampling=Resampling.bilinear
            )

            # Scale image transform
            transform = src.transform * src.transform.scale(
                (src.width / data.shape[-1]),
                (src.height / data.shape[-2])
            )
            
            # Read data to bands and remove 0.0 values
            VH_band = data[0]
            VH_band[VH_band == 0.0] = np.nan
            VV_band = data[1]
            rows, cols = VV_band.shape
            
            VVs.append(VV_band[position])
            VHs.append(VH_band[position])
            dates.append(date)

            i -= 1
    
    return VVs, VHs, dates

def extract_intersected_data(netcdf_path, target_shapefile_path):
    # Open the NetCDF file as an xarray.Dataset
    ds = xr.open_dataset(netcdf_path)

    # Load the target shapefile as a GeoDataFrame
    target_gdf = gpd.read_file(target_shapefile_path)

    # Convert the WKT geometries back to shapely geometries
    geometries = ds['geometry'].values
    geometries_shapely = [wkt.loads(geom) for geom in geometries]

    # Create a GeoDataFrame from the geometries
    gdf = gpd.GeoDataFrame({'geometry': geometries_shapely})
    gdf = gdf.set_crs('epsg:3067')
    target_gdf = target_gdf.set_crs('epsg:3067')

    gdf = gdf.to_crs('epsg:3067')
    target_gdf = target_gdf.to_crs('epsg:3067')

    # Perform the spatial join to find intersections with the target shapefile
    intersected_gdf = gpd.sjoin(gdf, target_gdf, how="inner", predicate='intersects')

    # Get the indices of the intersected geometries
    intersected_indices = intersected_gdf.index

    # Extract the intersected data from the xarray.Dataset
    intersected_data = ds.isel(geometry=intersected_indices)

    # Extract the specific variables and dates
    temperature = intersected_data['temperature']
    snows = intersected_data['snow']
    precipitation_amount = intersected_data['precipitation_amount']
    precipitation_intensity = intersected_data['precipitation_intensity']
    meteo_dates = intersected_data['time']
    dates = [pd.to_datetime(date).strftime('%Y-%m-%d') for date in meteo_dates.values]

    return temperature, snows, precipitation_amount, precipitation_intensity, dates


def main():
    
    args = read_arguments_from_file(os.path.join(os.getcwd(), 'arguments.txt'))
    timeseries = args.get('timeseries') == 'True'
    movingAverage = args.get('movingAverage') == 'True'
    movingAverageWindow = int(args.get('movingAverageWindow'))
    reflector = args.get('reflector') == 'True'
    
    
    if timeseries:

        source_path = sys.argv[1]
        path = sys.argv[2]
        bulkDownload = sys.argv[3].lower() == 'true'
        identifier = sys.argv[4]

        if not bulkDownload:
            data_path = os.path.join(path,identifier,'tiffs')
        else:
            data_path = os.path.join(path,'tiffs')

        masked_path = os.path.join(path,identifier,'masked_tiffs')
        path_to_shapefile = os.path.join(path, identifier, 'shapefile', f'{identifier}.shp')

        df = parse_file_info(data_path)
        print('File parsing completed.')

        if movingAverage:
            averaged_path = os.path.join(path,identifier,'averaged_tiffs')
            calculate_average_raster(df, data_path, averaged_path, movingAverageWindow)
            print('Averaging done.')
            mask_and_save_rasters(averaged_path, path_to_shapefile, masked_path)
        else:
            mask_and_save_rasters(data_path, path_to_shapefile, masked_path)
        print('Masking done.')
        gc.collect()

        # Save the bands as netCDF as well
        VV,VH, dates = extract_VV(masked_path)
        VV = resize_to_smallest(VV)
        VH = resize_to_smallest(VH)
        VV_xr = create_xarray(VV, dates, flip=True)
        VH_xr = create_xarray(VH, dates, flip=True)
        combined_xr = xr.combine_nested([VV_xr,VH_xr], concat_dim='band')
        combined_xr['band'] = ['VV', 'VH']
        combined_xr.to_netcdf(os.path.join(path,identifier,'VV_VH.nc'))

        # Calculate statistics
        calculate_statistics(VV, VH, dates, os.path.join(path,identifier,f'{identifier}_statistics.csv'))
        print('Statistics completed.')


        # Do reflector timeseries
        if reflector:
            upscale_factor = 10
            VV_max, VH_max, VV_arr, max_indices, filtered_indices, position = find_reflector(data_path, upscale_factor)
            make_location_fig(path,identifier,max_indices,filtered_indices,VV_arr,position)
            VV,VH, dates = extract_VV_meteo(data_path, position, upscale_factor)
        
        # Use either ready weather data, or download them again
        if bulkDownload:
            temperature, snows, precipitation_amount, precipitation_intensity, meteo_dates = extract_intersected_data(os.path.join(path,'weather.nc'), path_to_shapefile)
        else:
            temperature, snows, precipitation_amount,precipitation_intensity, meteo_dates = find_meteorological_data(data_path, path, identifier, path_to_shapefile)
        make_plot(path,identifier,temperature,precipitation_amount,snows,VV,VH,dates,meteo_dates, reflector)
        print('Plots created, analysis done. \n')
        
    else:
        print('Timeseries not done.')

if __name__ == "__main__":
    main()