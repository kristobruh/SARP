'''
This script does the following:
1. Read necessary arguments from the arguments.txt file.
2. Unzip all files in the folder to which the results were downloaded.
3. Loop through each .SAFE file, and if another .SAFE is found with matching orbit (composite image):
    a) Send those two to processing
    b) If no match is found, send only the one .SAFE to processing without slice assembly.
    
This script therefore does not do any processing itself, only unzips and send the files for further processing. This is done to clean the java temporary memory used by SNAP by terminating the processing script after each process. Otherwise the pipeline would choke after only a few processes.

In order to run this properly, ensure you have the following:
1. Updated arguments.txt to match with your parameters
2. Downloaded all the necessary files through download_from_asf.py script, or some other
3. Created a DEM of the target area through create_dem.py or some other way
4. loaded SNAP module (module load snap)
5. Assigned temporary directory for java (source snap_add_userdir $TMPDIR for interactive, source snap_add_userdir $LOCAL_SCRATCH for batch jobs)
6. Assigned enough memory to java (e.g. snap -J-xmx16G) 

Then you are good to run this through the command line interface!

NOTE: For now it has some hard-coded things specific to Finland, so refrain from using it in any other CRS' than epsg:3067.

'''

import os,sys, subprocess, shutil, csv, time, datetime

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


def process_sar_data(image1,image2, dataPath, pathToDem, pathToShapefile):
    """
    Caller function to the subscript which does the processing.
    
    Input:
    - image1 (str): Full path to the first .SAFE folder to be processed. 
    - image2 (str): Full path to the second .SAFE folder to be processed. Can be 'none' when no slice assembly is needed.
    """
    
    # Construct the command to run SarPipeline.py with the specified arguments
    command = [
        'python3', 'snap_process.py',
        image1, image2, dataPath, pathToDem, pathToShapefile
    ]
    
    # Run the command using subprocess
    subprocess.run(command)



def main():
    # Main function to call all sub-functions and subscripts.
    
    # ------- START ARGUMENT CALL --------
    source_path = sys.argv[1]
    path = sys.argv[2]
    bulkDownload = sys.argv[3].lower() == 'true'
    if not bulkDownload:
        identifier = sys.argv[4]
        dataPath = os.path.join(path,identifier,'tiffs')
        pathToShapefile = os.path.join(path,identifier,'shapefile',f'{identifier}.shp')
        pathToDem = os.path.join(path,identifier,f'{identifier}_dem.tif')
    else:
        dataPath = os.path.join(path,'tiffs')
        filename = os.path.basename(source_path)
        filename = os.path.splitext(filename)[0]
        pathToShapefile = os.path.join(path,f'{filename}.shp')
        pathToDem = os.path.join(path,f'{filename}_dem.tif')
        
    # ------- END ARGUMENT CALL -------- 
    
    
    # ------- START PROCESSING -------
    
    # Iterate through files in the folder
    for filename1 in os.listdir(dataPath):
        combined = False
        # Ensure that we're only working with .SAFE data
        if not filename1.endswith('.SAFE'):
            continue
        
        # Ensure that the file still exists after possible deletions
        if not os.path.exists(os.path.join(dataPath, filename1)):
            continue

        # Get the absolute orbit identifier
        orbit1 = filename1.split('_')[6]

        # Iterate through files again to compare with other files
        for filename2 in os.listdir(dataPath):
            # Ensure that we're not comparing the file with itself
            if filename1 == filename2:
                continue
            # Ensure that we're only working with .SAFE data
            if not filename2.endswith('.SAFE'):
                continue
                
            # Ensure that the file still exists after possible deletions
            if not os.path.exists(os.path.join(dataPath, filename2)):
                continue

            # Get the second absolute orbit identifier
            orbit2 = filename2.split('_')[6]

            # Check if the orbits match, then preform processing
            if orbit1 == orbit2:
                print(f'Sending to process: {filename1} and {filename2}')
                # Call the sub-script function and send the filenames to SarPipeline2.py
                process_sar_data(os.path.join(dataPath, filename1), os.path.join(dataPath, filename2), dataPath, pathToDem, pathToShapefile)
                # Remove processed .SAFEs to ensure that they're not double worked.
                shutil.rmtree(os.path.join(dataPath, filename1))
                shutil.rmtree(os.path.join(dataPath, filename2))
                combined = True
                # Break the second loop, move to next file in the first loop
                break
       
        # If no match is found after searching all files, perform processing on just the one image
        if not combined:
            print(f'Sending to process: {filename1}')
            process_sar_data(os.path.join(dataPath, filename1), 'none', dataPath, pathToDem, pathToShapefile) # Here none is given as the second image
            shutil.rmtree(os.path.join(dataPath, filename1))

    # ------- END PROCESSING -------


if __name__ == "__main__":
    main()