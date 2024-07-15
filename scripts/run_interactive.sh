#!/bin/bash

# Start measuring time
start=$(date +%s)


bulk_download=false
separate=false

while getopts ":s:r:bp" opt; do
  case ${opt} in
    s )
      source_path=${OPTARG}
      ;;
    r )
      data_path=${OPTARG}
      ;;
    b )
      bulk_download=true
      ;;
    p )
      separate=true
      ;;
    \? )
      echo "Usage: $0 [--source source_path] [--result data_path] [--bulk] [--separate]" >&2
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

if [[ ${source_path} == *.csv ]]; then
  bulk_download=false
fi

echo "Bulk download: $bulk_download, Separate polygons: $separate"

# Set the path to the folder containing the scripts
script_folder=$(dirname "$0")
module load geoconda
python download_packages.py

# Trap the termination signal and call the terminate function
terminate() {
    echo "Parent shell script terminated."
    exit 1
}
trap terminate SIGTERM
python initialize.py "$source_path" "$data_path" "$separate" "$bulk_download"
if [ $? -ne 0 ]; then
    exit 1
fi


if [ "$bulk_download" = true ]; then
    
    # Download all files over target area
    start_download=$(date +%s)
    python download_images.py "$source_path" "$data_path" "$bulk_download"
    end_download=$(date +%s)

    # Create DEM over the large area
    python download_dem.py "$source_path" "$data_path" "$bulk_download"
    
    # Download orbit files
    python download_orbits.py "$data_path" "$bulk_download"
    
    # Process all images, subset to greatest extent
    start_process=$(date +%s)
    module load snap
    source snap_add_userdir $data_path
    python3 process_images.py "$source_path" "$data_path" "$bulk_download"
    end_process=$(date +%s)
  
    
    module load geoconda
    for folder_path in "$data_path"/*/; do
        # Extract folder (id) name
        id=$(basename "$folder_path")
        if [ "$id" == "SLURM" ] || [ "$id" == "Error" ] || [ "$id" == "tiffs" ] || [ "$id" == "snap_cache" ] || [ "$id" == "*" ]; then
            continue
        fi
        echo "ID: $id"

        # Create timeseries of each target
        python timeseries.py "$source_path" "$data_path" "$bulk_download" "$id"
    done    

    runtime=$((end_download-start_download))
    echo "Download execution time: $runtime seconds"

    runtime=$((end_process-start_process))
    echo "Image process execution time: $runtime seconds"

    end=$(date +%s)
    runtime=$((end-start))
    echo "Script execution time: $runtime seconds"
    

else
 for folder_path in "$data_path"/*/; do
        # Extract folder (id) name
        id=$(basename "$folder_path")
        if [ "$id" == "SLURM" ] || [ "$id" == "Error" ] || [ "$id" == "snap_cache" ]; then
            continue
        fi
        echo "ID: $id"
        python download_from_asf.py "$source_path" "$data_path" "$bulk_download" "$id"
        python create_dem.py "$source_path" "$data_path" "$bulk_download" "$id"
        
        # Download orbit files
        python S1_orbit_download.py "$data_path" "$bulk_download" "$id"  
    
        module load snap
        source snap_add_userdir $data_path
        python3 iterate_sar.py "$source_path" "$data_path" "$bulk_download" "$id"
        
        module load geoconda
        python timeseries.py "$source_path" "$data_path" "$bulk_download" "$id"

    done
    end=$(date +%s)
    runtime=$((end-start))
    echo "Script execution time: $runtime seconds"
fi



