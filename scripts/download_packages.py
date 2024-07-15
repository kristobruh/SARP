import subprocess, sys

print('Ensuring all external packages are installed...')

try:
    import asf_search as asf
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "asf_search"])
    import asf_search as asf
    

try:
    from eof.download import download_eofs
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "sentineleof"])
    from eof.download import download_eofs
    
    
try:
    import rasterio
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "rasterio"])
    import rasterio
    
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
    
try:
    from fmiopendata.wfs import download_stored_query
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "fmiopendata"])
    from fmiopendata.wfs import download_stored_query

print('All good! \n')