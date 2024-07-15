import os, subprocess, sys, shutil, csv

try:
    from eof.download import download_eofs
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "sentineleof"])
    from eof.download import download_eofs

    
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

    
def download_orbit_files():    
    '''
    Download precise S1 ephemeris files. The process it two-pronged: first, all files are downloaded in bulk and saved to a temporary folder. Then, in order for SNAP to find them, they are moved to folders that correspond to the desired year and month.
    
    Input:
    
    Output: 
    Downloaded and sorted orbit files.
    '''
    
    # ------- START ARGUMENT CALL --------
    path = sys.argv[1]
    bulkDownload = sys.argv[2].lower() == 'true'
    if not bulkDownload:
        identifier = sys.argv[3]
        dataPath = os.path.join(path,identifier,'tiffs')
        orbit_folder = os.path.join(path, identifier, 'snap_cache/auxdata/Orbits/Sentinel-1/POEORB/S1A/')
    else:
        dataPath = os.path.join(path,'tiffs')
        orbit_folder = os.path.join(path, 'snap_cache/auxdata/Orbits/Sentinel-1/POEORB/S1A/')
   
    # ------- END ARGUMENT CALL -------- 
    
    # Create proper folder structure within the snap temporary folder
    dates = []
    sat = []
    for file in os.listdir(dataPath):
        if not file.endswith('.SAFE'):
            continue
        
        # Ensure that the file still exists after possible deletions
        if not os.path.exists(os.path.join(dataPath, file)):
            continue

        # Get the absolute orbit identifier
        date = file.split('_')[5]
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        hour = date[9:11]
        minute = date[11:13]
        second = date[13:15]
        
        date = f'{year}{month}{day}{hour}{minute}{second}'
        
        os.makedirs(os.path.join(orbit_folder,year,month), exist_ok=True)
        
        dates.append(date)
        sat.append('S1A')
        
    
    unsorted_folder = os.path.join(orbit_folder,'unsorted')
    os.makedirs(unsorted_folder, exist_ok=True)
    
    print('Downloading orbit files...')
    download_eofs(dates, sat, save_dir=unsorted_folder)
    
    
    
    # Sort orbit files to correct year and month
    for file in os.listdir(unsorted_folder):
        source = os.path.join(unsorted_folder, file)

        
        date = file.split('_')[-1]
        year = date[:4]
        month = date[4:6]

        destination = os.path.join(orbit_folder, year, month)

        shutil.move(source, destination)

    print("Orbit files sorted and moved to their respective directories. \n")
    
    
def main():
    
    args = read_arguments_from_file(os.path.join(os.path.dirname(os.getcwd()), 'arguments.csv'))
    applyOrbitFile = args.get('applyOrbitFile') == 'True'
    
    if applyOrbitFile:
        download_orbit_files()
        
    else:
        print('Not downloading orbit files. \n')
    
if __name__== "__main__":
    main()