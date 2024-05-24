import sys
import geopandas as gpd
import os
from shapely.geometry import Point
import shutil

def process_shapefiles(source_path, result_path, separate=True, bulkDownload=False):
    
    gdf = gpd.read_file(source_path)
    
    if separate:
        for index, row in gdf.iterrows():
            # Create folder name based on the 'id' column
            folder_name = str(row['id'])
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
    
    # Read the CSV file
    gdf = gpd.read_file(input_csv, delimiter='\t', header=0)

    # Convert GeoDataFrame to have Point geometries
    gdf['geometry'] = gdf.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    gdf = gdf.set_crs('epsg:4326')
    gdf = gdf.to_crs('epsg:3067')


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
        #polygon_gdf = polygon_gdf.to_crs('epsg:3067')
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


        
        
if __name__ == "__main__":
    # Get input arguments
    source_path = sys.argv[1]
    result_path = sys.argv[2]
    separate = sys.argv[3].lower() == 'true'
    bulkDownload = sys.argv[4].lower() == 'true'
    
    
    # Clear output
    #if os.path.isdir(result_path):
    #    shutil.rmtree(result_path)
        
    # Process input
    if source_path.endswith('.csv'):
        process_coordinates(source_path, result_path, bulkDownload)
        print("Coordinate processing complete.")
    else:
        process_shapefiles(source_path, result_path, separate, bulkDownload)
        print("Shapefile processing complete. \n")
    folder_slurm = os.path.join(result_path, 'SLURM')
    folder_error = os.path.join(result_path, 'Error')
    os.makedirs(folder_slurm, exist_ok=True)
    os.makedirs(folder_error, exist_ok=True)