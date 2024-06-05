import os, sys
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import box, Polygon
import fiona

def main():
    # Extract arguments from shellscript
    pathToTarget = sys.argv[1]
    pathToResult = sys.argv[2] 
    bulkDownload = sys.argv[3].lower() == 'true'
    if not bulkDownload:
        identifier = sys.argv[4]

    # Create paths and folders
    if bulkDownload:
        filename = os.path.basename(pathToTarget)
        filename = os.path.splitext(filename)[0]
        pathToDem = os.path.join(pathToResult, f'{filename}_dem.tif')
        pathToShapefile = os.path.join(pathToResult, f'{filename}.shp')

    else:
        pathToDem = os.path.join(pathToResult, identifier, f'{identifier}_dem.tif')
        pathToShapefile = os.path.join(pathToResult, identifier, 'shapefile', f'{identifier}.shp')

    # Get DEM area of interest
    gdf = gpd.read_file(pathToShapefile)

    # Change to 3067
    if gdf.crs != 'epsg:3067':
        gdf = gdf.to_crs(epsg=3067)

    # Create a 500m buffer around the shapefile
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


    # Call the virtual raster with spahefile inputs and save it
    vrt_path = "/appl/data/geo/mml/dem2m/dem2m_direct.vrt"

    with rasterio.open(vrt_path) as src:
        rst = src.read(window=from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], src.transform), 
                       boundless=True, fill_value=0)
        # Extract DEM CRS
        crs = src.crs

    # Create a new transformation matrix for the raster    
    xmin = bounds[0]
    ymax = bounds[3]
    pixel_size_x = (bounds[2] - bounds[0]) / rst.shape[2]
    pixel_size_y = (bounds[3] - bounds[1]) / rst.shape[1]
    transform = from_origin(xmin, ymax, pixel_size_x, pixel_size_y)

    # SAve DEM
    print(f"Writing DEM...")
    with rasterio.open(pathToDem, 'w', driver='GTiff', 
                       width=rst.shape[2], height=rst.shape[1], 
                       count=rst.shape[0], dtype=rst.dtype, 
                       crs=crs, transform=transform,
                       nodata=-9999) as dst:
        dst.write(rst)
    print(f"DEM saved. \n")
    
if __name__ == "__main__":
    main()
