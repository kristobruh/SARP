'''
This script does all the actual processing, and is run by calling it from the parent script (process_images.py). Running it standalone won't work.
Running this processing takes a considerable amount of memory, and that is why it is called separately each time in order to force clean the temp memory between processes.
'''

import os, gc, subprocess, sys, argparse, csv
from snappy import HashMap, GPF, ProductIO
from snapista import Operator
import jpy

try:
    import geopandas as gpd
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "geopandas"])
    import geopandas as gpd

try:
    from shapely.geometry import Polygon
    from shapely.ops import transform
    from shapely.wkt import loads
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "shapely"])
    from shapely.geometry import Polygon
    from shapely.ops import transform
    from shapely.wkt import loads

try:
    import pyproj
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyproj"])
    import pyproj

    
    
    
def read_arguments_from_file(file_path):
    '''
    Helper function to read the arguments.csv file.
    
    Input:
    - file_path (str) - Full path to the arguments file.
    
    Output: 
    arguments (dict) - Dictionary of the arguments.
    '''
    arguments = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            if row and not row[0].startswith('#'):
                arg_name, arg_value = row
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


def do_calibration(source, polarization, pols, complexOutput):
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
    if complexOutput:
        #parameters.put('outputSigmaBand', False)
        parameters.put('outputImageInComplex', True)
    else:
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
    output (productIO) - Split product.
    ''' 
    print('\tSplitting SLC...')
    parameters = HashMap()
    parameters.put('wktAoi', wkt)
    output = GPF.createProduct('TOPSAR-Split', parameters, source)
    
    return output

def TOPSAR_deburst(source):
    '''
    Deburst image for clearer picture.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Debursted product.
    ''' 
    print('\tDebursting SLC...')
    parameters = HashMap()
    output = GPF.createProduct('TOPSAR-Deburst', parameters, source)
    
    return output

def polarimetric_speckle_filtering(source,filterResolution):
    '''
    Apply polarimetric speckle filter.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Polarimetrically speckle filtered product.
    ''' 
    print('\tPolarimetric spekle filtering...')
    parameters = HashMap()
    parameters.put('filter','Refined Lee Filter')
    parameters.put('numLooksStr','1')
    parameters.put('filterSize',filterResolution)
    resolution = f'{filterResolution}x{filterResolution}'
    parameters.put('windowSize',resolution)
    output = GPF.createProduct('Polarimetric-Speckle-Filter', parameters, source)
    
    return output

def polarimetric_decomposition(source):
    '''
    Calculate entropy, anisotropy, and alpha of polSAR.
    
    Input:
    source (productIO) - SAR image with auxiliary files.
    
    Output:
    output (productIO) - Subsetted product.
    ''' 
    print('\tCalculating entropy, anisotropy, and alpha...')
    parameters = HashMap()
    parameters.put('decomposition','H-Alpha Dual Pol Decomposition')
    parameters.put('outputHAAlpha','true')
    parameters.put('windowSize', 5)
    parameters.put('outputTouziParamSet0', 'true')
    parameters.put('outputHuynenParamSet0', 'true')
    output = GPF.createProduct('Polarimetric-Decomposition', parameters, source)
    
    return output   


def polarimetric_matrices(source):
    
    
    print('\tCreating polarimetric C2 matrix...')
    parameters = HashMap()
    parameters.put('matrix','C2')
    output = GPF.createProduct('Polarimetric-Matrices', parameters, source)
    
    return output
    
def polarimetric_parameters(source):
    
    
    print('\tCalculating Stokes parameters...')
    parameters = HashMap()
    parameters.put('outputStokesVector','false')
    parameters.put('outputDegreeOfPolarization', 'true')
    parameters.put('outputDegreeOfDepolarization', 'true')
    parameters.put('outputDegreeOfCircularity', 'true')
    parameters.put('outputDegreeOfEllipticity', 'true')
    parameters.put('outputCPR', 'true')
    parameters.put('outputLPR', 'true')
    parameters.put('outputRelativePhase', 'false')
    parameters.put('outputAlphas', 'false')
    parameters.put('outputConformity', 'false')
    parameters.put('outputPhasePhi', 'false')
    parameters.put('windowSizeXStr', '5')
    parameters.put('windowSizeYStr', '5')
    output = GPF.createProduct('CP-Stokes-Parameters', parameters, source)
    
    return output


def stack(source1,source2):
    
    print('\tStacking polSAR parameters...')
    
    product_set = []
    product_set.append(source1)
    product_set.append(source2)
    parameters = HashMap()
    parameters.put('resamplingType','NONE')
    parameters.put('initialOffsetMethod','Orbit')
    parameters.put('extent','Master')
    output = GPF.createProduct('CreateStack', parameters, product_set)
    
    return output


def main():
    
    # --------START READ VARIABLES ---------
    # Read arguments from the text file
    args = read_arguments_from_file(os.path.join(os.path.dirname(os.getcwd()), 'arguments.csv'))
    process = args.get('process')
    if process == 'GRD':
        applyOrbitFile = True
        thermalNoiseRemoval = True
        calibration = True
        complexOutput = False
        speckleFiltering = True
        filterResolution = 5
        terrainCorrection = True
        terrainResolution = 10.0
        bandMaths = False
        linearToDb = True
        slcSplit = False
        slcDeburst = False
        polarimetricSpeckleFiltering = False
        polarimetricParameters = False
        
    elif process == 'SLC':
        applyOrbitFile = True
        thermalNoiseRemoval = False
        calibration = True
        complexOutput = True
        speckleFiltering = True
        filterResolution = 5
        terrainCorrection = True
        terrainResolution = 10.0
        bandMaths = False
        linearToDb = False
        slcSplit = True
        slcDeburst = True
        polarimetricSpeckleFiltering = False
        polarimetricParameters = False
        
    elif process == 'polSAR':
        applyOrbitFile = True
        thermalNoiseRemoval = False
        calibration = True
        complexOutput = True
        speckleFiltering = False
        filterResolution = 5
        terrainCorrection = True
        terrainResolution = 10.0
        bandMaths = False
        linearToDb = False
        slcSplit = False
        slcDeburst = True
        polarimetricSpeckleFiltering = True
        polarimetricParameters = True
        
        
    else:
        polarization = args.get('polarization') 
        slcSplit = args.get('slcSplit') == 'True'
        applyOrbitFile = args.get('applyOrbitFile') == 'True'
        thermalNoiseRemoval = args.get('thermalNoiseRemoval') == 'True'
        calibration = args.get('calibration') == 'True'
        complexOutput = args.get('complexOutput') == 'True'
        slcDeburst = args.get('slcDeburst') == 'True'
        speckleFiltering = args.get('speckleFiltering') == 'True'
        polarimetricSpeckleFiltering = args.get('polarimetricSpeckleFiltering') == 'True'
        polarimetricParameters = args.get('polarimetricParameters') == 'True'
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
            try:
                product = TOPSAR_split(product,wkt)
            except RuntimeError:
                print('Target does not overlap with any bursts.')
                sys.exit()
        
        # 0.5: APPLY ORBIT FILE 
        if applyOrbitFile:
            product = apply_orbit_file(product)
        
        #1: REMOVE THERMAL NOISE
        if thermalNoiseRemoval:
            product = do_thermal_noise_removal(product)
        
        
    #2: CALIBRATE
    if calibration:
        product = do_calibration(product, polarization, pols, complexOutput)
        
        
    if slcDeburst:
        product = TOPSAR_deburst(product)


    #3: SPECKLE FILTER
    if speckleFiltering:
        filterType = 'Lee'
        product = do_speckle_filtering(product, filterType, filterResolution)
        
    if polarimetricSpeckleFiltering:
        product = polarimetric_speckle_filtering(product,filterResolution)

    if polarimetricParameters:
        product_HAAlpha = polarimetric_decomposition(product)
        #C2_matrix = polarimetric_matrices(product)
        product_stokes = polarimetric_parameters(product)
        product = stack(product_HAAlpha, product_stokes)


    #4: TERRAIN CORRECTION
    #define epsg:3067. This is atm hard-coded.
    proj = '''PROJCS["ETRS89 / TM35FIN(E,N)", GEOGCS["ETRS89", DATUM["European Terrestrial Reference System 1989", SPHEROID["GRS 1980", 6378137.0, 298.257222101, AUTHORITY["EPSG","7019"]], TOWGS84[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], AUTHORITY["EPSG","6258"]], PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], UNIT["degree", 0.017453292519943295], AXIS["Geodetic longitude", EAST], AXIS["Geodetic latitude", NORTH], AUTHORITY["EPSG","4258"]], PROJECTION["Transverse_Mercator", AUTHORITY["EPSG","9807"]], PARAMETER["central_meridian", 27.0], PARAMETER["latitude_of_origin", 0.0], PARAMETER["scale_factor", 0.9996], PARAMETER["false_easting", 500000.0], PARAMETER["false_northing", 0.0], UNIT["m", 1.0], AXIS["Easting", EAST], AXIS["Northing", NORTH], AUTHORITY["EPSG","3067"]]'''
    if terrainCorrection:
        try:
            product = do_terrain_correction(product, proj, pathToDem, terrainResolution)
        except RuntimeError:
            print('Target does not overlap with the image.')
            sys.exit()
          
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
        
        
    # Get relevant metadata
    product_type = product.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('PRODUCT_TYPE').getData()
    direction = product.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('PASS').getData()
    rel_orbit = product.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('REL_ORBIT').getData()
    look = product.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('antenna_pointing').getData()
    
    #print(f'Product type: {product_type}, Orbit: {direction}, Relative orbit: {rel_orbit}, Look: {look}')
    
    
    #metadata_root = product.getMetadataRoot()
    #for element in metadata_root.getElements():
    #    for attribute in element.getAttributes():
    #        attribute_name = attribute.getName()
    #        attribute_value = attribute.getData()
    #        print(f"Attribute Name: {attribute_name}, Value: {attribute_value}")

    #9: WRITE
    with open(os.path.join(os.path.dirname(dataPath), 'band_names.csv'), mode='w', newline='') as file:
        writer = csv.writer(file)
        for band in product.getBands():
            if process == 'polSAR':
                band_name = band.getName().split('_')[0]
            else:
                band_name = band.getName().split('_')[1]
            writer.writerow([band_name])


    print('Writing...')
    filename = os.path.basename(image1)
    if slcDeburst:
        time_str = filename.split('_')[5][:8]
    else:
        time_str = filename.split('_')[4][:8]
    output_filename = f'{time_str}_{product_type}_{direction}_{rel_orbit}_{look}_processed.tif'
    ProductIO.writeProduct(product, os.path.join(dataPath, output_filename), 'GeoTIFF')
    
    print('Processing done. \n')
    gc.collect()

    # -------- END OF PROCESSING ----------

if __name__== "__main__":
    main()