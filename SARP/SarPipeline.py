'''
This script does all the actual processing, and is run by calling it from the parent script (iterate_sar.py). Running it standalone won't work.

The general processing pipeline is:
0.5. Extract relevant arguments from the text file and sent by the parent script
If two images need to be combined:
    1.1 Remove thermal noise from both
    1.2 Assemble the slices to one image
Else:
    1. Remove thermal noise from just one image
2. Calibrate to get VH and VV values
3. Speckle filter to desired filter (NOTE: if changed, some parameters will be needed to be added and removed)
4. Terrain correct
5. Convert to dB
6. Subset to the boundaries defined by the shapefile
7. Calculate band maths for some indicator value
8. Combine the VV+VH and band maths bands
9. Write to a GeoTIFF file.

Running this processing takes a considerable amount of memory, and that is why it is called separately each time in order to force clean the temp memory between processes.

There are some functions which are not used in this particular process, but I kept them for possible future use.

'''

import os, gc
from snappy import HashMap, GPF, ProductIO
from snapista import Operator
import jpy
import shutil
import subprocess
import sys
import argparse

# These are not a part of SNAP, thus they will be installed locally to the user and then imported
# Needed for reading shapefiles properly
try:
    import geopandas as gpd
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "geopandas"])
    import geopandas as gpd

# Needed for shapefile transformations and boundary definitions
try:
    from shapely.geometry import box, Polygon
    from shapely.ops import transform
    from shapely.wkt import loads
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "shapely"])
    from shapely.geometry import box, Polygon
    from shapely.ops import transform
    from shapely.wkt import loads

try:
    from rasterio.windows import from_bounds
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "rasterio"])
    from rasterio.windows import from_bounds

try:
    import pyproj
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyproj"])
    import pyproj

try:
    import psutil
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "psutil"])
    import psutil

    
    
    
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

def parse_arguments():
    """
    Parse arguments given by the parent script.
    
    Input:
    - Arguments defined in the parent script, full paths to images to be processed.
    
    Output:
    - Dictionary containing the arguments.
    """
    parser = argparse.ArgumentParser(description="Process SAR data.")
    parser.add_argument("image1", type=str, help="Path to the first SAR image.")
    parser.add_argument("image2", type=str, help="Path to the second SAR image.")
    parser.add_argument("pathToResult", type=str, help="Path to the results folder.")
    parser.add_argument("pathToDem", type=str, help="Path to DEM.")
    parser.add_argument("pathToShapefile", type=str, help="Path to shapefile.")
    return parser.parse_args()


def apply_orbit_file(source):
    """
    Apply prceise ephemeris data on orbits, as downloaded through S1_orbit_download.py.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    source (productIO) - SAR image with corrected orbit data.
    """
    print('\tApplying orbit file...')
    # Define parameters
    parameters = HashMap()
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', 3)
    parameters.put('continueOnFail', 'true')
    
    # Do the orbit file application
    output = GPF.createProduct('Apply-Orbit-File', parameters, source)
    return output


def do_slice_assembly(sources):
    '''
    Assemble two bands from different sources into a single product.
    This could be modified to take in any number 
    
    Inputs:
    sources (list) - List of SAR images with auxiliary files.
    
    Output:
    output (productIO) - Assembled product.
    '''
    print('\tAssembling images...')
    
    # Create HashMap for parameters
    parameters = HashMap()
    # Assemble all polarizations
    parameters.put('selctedPolarizations','')
    
    # Create the merged product
    output = GPF.createProduct('SliceAssembly', parameters, sources)
    
    return output



def do_thermal_noise_removal(source):
    '''
    Remove thermal noise from image, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Thermally corrected SAR image.
    ''' 
    
    print('\tThermal noise removal...')
    # Define parameters
    parameters = HashMap()
    parameters.put('removeThermalNoise', True)
    
    # Do the thermal noise removal
    output = GPF.createProduct('ThermalNoiseRemoval', parameters, source)
    return output


def do_calibration(source, polarization, pols):
    '''
    Calibrate SAR image based on the configuration files within, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Calibrated SAR image.
    ''' 
    print('\tCalibration...')
    
    # Define parameters
    parameters = HashMap()
    
    #if polarization == 'DH':
    #    parameters.put('sourceBands', 'Intensity_HH,Intensity_HV')
    #elif polarization == 'DV':
    #    parameters.put('sourceBands', 'Intensity_VH,Intensity_VV')
    #elif polarization == 'SH' or polarization == 'HH':
    #    parameters.put('sourceBands', 'Intensity_HH')
    #elif polarization == 'SV':
    #    parameters.put('sourceBands', 'Intensity_VV')
    #else:
    #    print("different polarization!")
    #parameters.put('selectedPolarisations', pols)

    parameters.put('outputImageInComplex', False)
    parameters.put('outputSigmaBand', True)
    parameters.put('outputGammaBand', False)
    parameters.put('outputBetaBand', False)
    
    parameters.put('outputImageScaleInDb', False)
    output = GPF.createProduct("Calibration", parameters, source)
    return output


#c) Speckle filter
def do_speckle_filtering(source, filterType, filterResolution):
    '''
    Speckle filter SAR image based on the configuration files within, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    filterType (str) - Name of the filtering method.
    
    Output:
    output (productIO) - Speckle filtered product.
    ''' 
    print('\tSpeckle filtering...')
    parameters = HashMap()
    parameters.put('filter', filterType)
    parameters.put('filterSizeX', filterResolution)
    parameters.put('filterSizeY', filterResolution)
    output = GPF.createProduct('Speckle-Filter', parameters, source)
    return output


def do_terrain_correction(source, proj, pathToDem, terrainResolution):
    '''
    Terrain corrected SAR image based on the configuration files within, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    proj (str) - Projection metadata.
    pathToDEM (str) - path to external DEM which will be used in the correction.
    
    Output:
    output (productIO) - Terrain corrected product.
    ''' 
    print('\tTerrain correction...')
    parameters = HashMap()
    parameters.put('demName', 'External DEM')
    parameters.put('externalDEMFile',pathToDem)
    parameters.put('externalDEMNoDataValue', 0.0)
    parameters.put('externalDEMApplyEGM','true')
    parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('mapProjection', proj)
    parameters.put('saveProjectedLocalIncidenceAngle', True)
    parameters.put('saveSelectedSourceBand', True)
    parameters.put('pixelSpacingInMeter', terrainResolution)
    output = GPF.createProduct('Terrain-Correction', parameters, source)
    return output


def do_ellipsoid_correction(source, proj, downsample):
    #NOT OPERATIONAL! Just a template for possible future needs.
    print('\tEllipsoid correction...')
    parameters = HashMap()
    parameters.put('demName', 'External DEM')
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('mapProjection', proj)
    parameters.put('saveProjectedLocalIncidenceAngle', True)
    parameters.put('saveSelectedSourceBand', True)
    parameters.put('pixelSpacingInMeter', 10.0)
    output = GPF.createProduct('Terrain-Correction', parameters, source)
    return output


def do_linear_to_db(source):
    '''
    Convert the linear values to dB, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Product with dB values.
    ''' 
    print('\tTo dB...')
    parameters = HashMap()
    parameters.put('sourceBands', 'Sigma0_VH,Sigma0_VV')
    output = GPF.createProduct('LinearToFromdB', parameters, source)
    return output


def do_subset(source, wkt):
    '''
    Subset SAR image to a wkt, based on snappy.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    wkt (str) - WKT of the subset area, given in WGS84 projection.
    
    Output:
    output (productIO) - Subsetted product.
    ''' 
    print('\tSubsetting...')
    parameters = HashMap()
    parameters.put('geoRegion', wkt)
    output = GPF.createProduct('Subset', parameters, source)
    return output

def do_mosaicing(inputs, proj, wkt):
    '''
    Mosaic a collection of images, based on snappy.
    
    NOTE: This operation removes time information, as it is meant to be used with images of different acquisition dates. 
    Thus, for assembling images of same orbit, use do_slice_assembly.

    
    Input:
    inputs (list) - A list of images to be mosaiced, as filepath. Can be changed to list of ProductIOs by commenting the
    code which transforms them to ProductIOs later on.
    proj (str) - Projection string that defines the crs, currently hard-coded.
    wkt (str) - WKT of the subset area, given in WGS84 projection.
    
    Output:
    output (productIO) - Mosaiced product.
    ''' 
    print('\tMosaicing...')
    
    # Extract bounds
    geometry = loads(wkt)
    min_x, min_y, max_x, max_y = geometry.bounds
    
    parameters = HashMap()
    
    # Define the band variables
    Variable = jpy.get_type('org.esa.snap.core.gpf.common.MosaicOp$Variable')
    vars = jpy.array('org.esa.snap.core.gpf.common.MosaicOp$Variable', 2)
    vars[0] = Variable('Sigma0_VH_db','Sigma0_VH_db')
    vars[1] = Variable('Sigma0_VV_db','Sigma0_VV_db')
    parameters.put('variables', vars)
    
    
    # Set other parameters
    parameters.put('combine', 'OR')  # Combine condition
    parameters.put('crs', proj)  # CRS
    parameters.put('orthorectify', False)
    parameters.put('elevationModelName', 'SRTM 3Sec')
    parameters.put('resampling', 'Nearest')
    parameters.put('westBound', min_x)
    parameters.put('eastBound', max_x)
    parameters.put('southBound', min_y)
    parameters.put('northBound', max_y)
    parameters.put('pixelSizeX', 10.0)
    parameters.put('pixelSizeY', 10.0)
    
    # Load input files as SNAP Product objects. Comment if they are already ProductIOs.
    products = [ProductIO.readProduct(file) for file in inputs]
    
    # Create the mosaic product
    output = GPF.createProduct('Mosaic', parameters, *products)
    
    # Legacy code, TODO: remove each source product.
    #os.remove(input1)
    #os.remove(input2)
    
    return output


def shapefile_to_wkt(pathToShapefile, epsg):
    '''
    Create a wkt of bounds out of a shapefile. NOTE: the wkt is of the bounds, not the exact shapefile.
    
    Inputs:
    - pathToShapefile (str): Full path to the shapefile.
    - epsg (str): The projection in which the wkt is presented. Example: 'epsg:3067'
    
    Output:
    - wkt (polygon) - Polygon object in wkt format.
    '''
    gdf = gpd.read_file(pathToShapefile)
    crs = gdf.crs
    
    #change to 3067 to create a 500m buffer
    if crs != 'epsg:3067':
        gdf = gdf.to_crs(epsg=3067)
        
    # Calculate the outer bounds of all polygons    
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

    buffer = 500
    bounds = (
        bounds[0] - buffer,
        bounds[1] - buffer,
        bounds[2] + buffer,
        bounds[3] + buffer
    )
    
    xmin, ymin, xmax, ymax = bounds
    # Create a polygon from the bounds
    polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])

    # Convert the polygon to WKT
    wkt = polygon.wkt

    # Change projection if necessary
    if crs != epsg:
        project = pyproj.Transformer.from_proj(
            pyproj.Proj(crs), 
            pyproj.Proj(epsg), 
            always_xy=True
        ).transform
        
        polygon = transform(project, polygon)
        
        wkt = polygon.wkt
    
    
    return wkt



def do_band_maths(source, expression):
    '''
    Do band maths based on hard-coded parameters.
    
    Inputs:
    - source (ProductIO): SAR image with auxiliary files.
    
    Output:
    - product (ProductIO): SAR image with ONLY THE BAND MATHS BAND.
    '''
   
    print('\tBand maths...')
    
    # Get the band descriptor class
    BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')

    # Create a new BandDescriptor object for the target band
    target_band = BandDescriptor()
    target_band.name = 'target_band'  # Name of the target band
    target_band.type = 'float32'  # Data type of the target band
    target_band.expression = expression  # Expression for band math operation

    # Create an array of BandDescriptor objects
    targetBands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = target_band

    # Create a HashMap to store parameters
    parameters = HashMap()
    parameters.put('targetBands', targetBands)

    # Create the BandMaths operation
    product = GPF.createProduct('BandMaths', parameters, source)

    return product
   
            
def do_band_merge(source1, source2):
    '''
    Merge bands from two images to a single product. Necessary after band maths.
    
    Inputs:
    - source1 (ProductIO): First SAR image with auxiliary files.
    - source2 (ProductIO): Second SAR image with auxiliary files.
    
    Output:
    output (productIO) - Merged product.
    '''
    
    print('\tMerging bands...')
    
    # Create HashMap for parameters
    parameters = HashMap()
    
    
    # Create the merged product
    output = GPF.createProduct('BandMerge', parameters, source1, source2)
    
    return output



def TOPSAR_split(source,wkt):
    '''
    Select only the desired subswaths within an SLC image.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    wkt (str) - WKT of the subset area, given in WGS84 projection.
    
    Output:
    output (productIO) - Subsetted product.
    ''' 
    print('\tSplitting SLC...')
    parameters = HashMap()
    parameters.put('wktAoi', wkt)
    output = GPF.createProduct('TOPSAR-Split', parameters, source)
    
    return output

def TOPSAR_deburst(source):
    '''
    Select only teh desired subswaths within an SLC image.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    wkt (str) - WKT of the subset area, given in WGS84 projection.
    
    Output:
    output (productIO) - Subsetted product.
    ''' 
    print('\tDebursting SLC...')
    parameters = HashMap()
    output = GPF.createProduct('TOPSAR-Deburst', parameters, source)
    
    return output
    



def main():
    
    # --------START READ VARIABLES ---------
    # Read arguments from the text file
    args = read_arguments_from_file(os.path.join(os.getcwd(), 'arguments.txt'))
    polarization = args.get('polarization')
    
    
    slcSplit = args.get('slcSplit') == 'True'
    applyOrbitFile = args.get('applyOrbitFile') == 'True'
    thermalNoiseRemoval = args.get('thermalNoiseRemoval') == 'True'
    calibration = args.get('calibration') == 'True'
    slcDeburst = args.get('slcDeburst') == 'True'
    speckleFiltering = args.get('speckleFiltering') == 'True'
    filterResolution = args.get('filterResolution')
    terrainCorrection = args.get('terrainCorrection') == 'True'
    terrainResolution = args.get('terrainResolution')
    bandMaths = args.get('bandMaths') == 'True'
    bandMathExpression = args.get('bandMathsExpression')
    linearToDb = args.get('linearToDb') == 'True'
    
    
    # Read arguments from the parent script
    args = parse_arguments()
    image1 = args.image1
    image2 = args.image2
    pathToShapefile = args.pathToShapefile
    dataPath = args.pathToResult
    pathToDem = args.pathToDem
    outPath = dataPath
    
    #print(f'Working on {image1} and {image2}.')
    
    # ---------END READ VARIABLES ----------
    
    
    
    
    
    # --------START OF PROCESSING -----------
    
    # Enable trash disposal, helps with memory issues
    gc.enable()
    gc.collect()


    ## Extract mode, product type, and polarizations from filename
    folder = os.path.basename(image1)
    modestamp = folder.split("_")[1]
    productstamp = folder.split("_")[2]
    
    if productstamp == 'GRDH':
        polstamp = folder.split("_")[3]
    elif productstamp == 'SLC':
        polstamp = folder.split("_")[4]
        print(polstamp)
    polarization = polstamp[2:4]
    
    if polarization == 'DV':
        pols = 'VH,VV'
    elif polarization == 'DH':
        pols = 'HH,HV'
    elif polarization == 'SH' or polarization == 'HH':
        pols = 'HH'
    elif polarization == 'SV':
        pols = 'VV'
    else:
        print("Polarization error!")

        

        
    
    # If there are two images, remove noise first and then assemble them
    if image2 != 'none':
    
        # Read files to appropriate format
        product1 = ProductIO.readProduct(image1)
        product2 = ProductIO.readProduct(image2)
        
        #0.5 APPLY ORBIT FILE
        if applyOrbitFile:
            product1 = apply_orbit_file(product1)
            product2 = apply_orbit_file(product2)

        #1: REMOVE THERMAL NOISE
        product1 = do_thermal_noise_removal(product1)
        product2 = do_thermal_noise_removal(product2)

        # Create a list of the products to be assembled
        products =[]
        products.append(product1)
        products.append(product2)
        
        #1.5: SLICE ASSEMBLE
        product = do_slice_assembly(products)
        
        # Some housekeeping
        del product1
        del product2
    
    # If there is only one image, proceed normally
    else:
        # Read file to appropriate format
        product = ProductIO.readProduct(image1)
        
        
        if slcSplit:
            wkt = shapefile_to_wkt(pathToShapefile, 'epsg:4326')
            product = TOPSAR_split(product,wkt)
        
        # 0.5: APPLY ORBIT FILE 
        if applyOrbitFile:
            product = apply_orbit_file(product)
        
        #1: REMOVE THERMAL NOISE
        if thermalNoiseRemoval:
            product = do_thermal_noise_removal(product)
        
        
    #2: CALIBRATE
    if calibration:
        product = do_calibration(product, polarization, pols)
        
        
    if slcDeburst:
        product = TOPSAR_deburst(product)


    #3: SPECKLE FILTER
    if speckleFiltering:
        filterType = 'Lee'
        do_speckle_filtering(product, filterType, filterResolution)


    #4: TERRAIN CORRECTION
    #define epsg:3067. This is atm hard-coded.
    proj = '''PROJCS["ETRS89 / TM35FIN(E,N)", GEOGCS["ETRS89", DATUM["European Terrestrial Reference System 1989", SPHEROID["GRS 1980", 6378137.0, 298.257222101, AUTHORITY["EPSG","7019"]], TOWGS84[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], AUTHORITY["EPSG","6258"]], PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], UNIT["degree", 0.017453292519943295], AXIS["Geodetic longitude", EAST], AXIS["Geodetic latitude", NORTH], AUTHORITY["EPSG","4258"]], PROJECTION["Transverse_Mercator", AUTHORITY["EPSG","9807"]], PARAMETER["central_meridian", 27.0], PARAMETER["latitude_of_origin", 0.0], PARAMETER["scale_factor", 0.9996], PARAMETER["false_easting", 500000.0], PARAMETER["false_northing", 0.0], UNIT["m", 1.0], AXIS["Easting", EAST], AXIS["Northing", NORTH], AUTHORITY["EPSG","3067"]]'''
    if terrainCorrection:
        product = do_terrain_correction(product, proj, pathToDem, terrainResolution)

    #5 COVERT TO DB
    if linearToDb:
        product = do_linear_to_db(product)

    #6: SUBSET
    wkt = shapefile_to_wkt(pathToShapefile, 'epsg:4326')
    product = do_subset(product, wkt)

    #7: BAND MATHS
    if bandMaths:
        maths = do_band_maths(product, bandMathExpression)
        product = do_band_merge(product, maths)
    

    #9: WRITE
    print('Writing...')
    # Cut name to only until date of acquisition
    filename = os.path.basename(image1)
    time_str = filename.split('_')[4][:8]
    output_filename = f'{time_str}_processed.tif'
    ProductIO.writeProduct(product, os.path.join(dataPath, output_filename), 'GeoTIFF')
    #ProductIO.writeProduct(product, dataPath + f'/{folder[:-47]}_processed', 'GeoTIFF')
    print('Processing done. \n')
    gc.collect()

    # -------- END OF PROCESSING ----------

if __name__== "__main__":
    main()