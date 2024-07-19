## Dependencies
This program is configured for CSC's Puhti environment. As such, it uses modules _geoconda_ and _snap_, along with a few external packages that are installed locally. The packages are:

- fmiopendata
- asf_search
- sentieneleof

Account authentification is needed in order to use asf_search and sentineleof, and thus you should create one (it's free!).

## 0. Create and verify Eathdata account
You need to have a verified Earthdata account with appropriate permssions in order to download images and orbit files. You can create the account [here](https://asf.alaska.edu/how-to/data-basics/get-started-with-an-earthdata-login-account/).

Then verify the account through email.

After doing so, you need to give permissions to ASF to download data. This can be done through [Earthdata profile page](https://urs.earthdata.nasa.gov/profile).

Sign in to you account, and navigate to **applications --> authorized apps**. Then click APPROVE MORE APPLICATIONS, search for "Alaska Satellite Facility Data Access", and give it authorization.

Once created, go to the base folder of you puhti account through the command line, and create a file named .netrc:

```
cd
nano .netrc
```

Then, write the following info in the file:

```
machine urs.earthdata.nasa.gov
 login <your username>
 password <your password>

```

Note that there should be a space before 'login' and 'password'. Once this is done, write `chmod 600 ~/.netrc` to the command line to restrict access to just the user. Now your account authentification process is complete!

## 1. Clone repository
Use `git clone https://gitlab.com/fgi_nls/kauko/chade/sarp.git` to clone the repository to a destination of your liking.

## 2. Set up input shapefile
You can use `example_target.gpkg` to try out the script, or use your own target. .shp and .gpgk files, as well as coordinate csv's, are accepted as input. For coordinate csv's, the input should be, all separated by tabs:

| name | lat | lon | alt |
|----------|----------|----------|----------|
| EXAMPLE NAME | 60.22912067326671 | 19.951266738151517 | 53.21935461927205|


## 3. Configure arguments
In `arguments.txt`,set up your preferred arguments. It is good to start with a short timeframe, e.g. 10 days and `processingLevel GRD_HD` and `process GRD`, to configure the packages. See variables page for more descriptions on the parameters. Note: If you use a predefined process, there is no need to define the individual parameters separately. 


## 4a. Run using CLI:
To run, you need to navigate to sarp/scripts/. The basic command is: 

```<run type> <script name> -s <source file> -r <result folder> -b (bulk download) -p (parse input file) ```

Source file path and results folder path are mandatory. Optional commands include:
- Bulk download `-b`: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately. This will drastically increase processing times, so use it sparingly.
- Parse shapefile `-p`: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile. Usually it is wise to enable this for individual parcel analysis.

**Interactive**

Before running the script in interactive, start a new job by `sinteractive -i`, and set up your parameters. The script is partly parallelized, so several cores is recommended, and at least 12GB of memory.

Example for running interactive: 

`bash run_interactive.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/ -b -p `



**Batch**

`sbatch run_batch.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/  -b -p`

If you run the script in batch process mode, remember to set up the batch process paramters in `run_batch.sh`. It is recommended to first run it in interactive to ensure that all works.

For some example commands, see **command.txt**.


## 4b. Run using Snakemake:
Again, navigate to sarp/scripts/. Set up the input parameters (source, target directory, bulk processing, separating) in config.yaml found in the folder. After that, in your CLI either write:

`module load snakemake`

`snakemake --cores 4`

for interactive process, or:

`sbatch run_batch_snakemake.sh`

for batch processing. Just remember to configure the batch process file parameters the same way as in regular batch processing.

Please note that `bulk_download: false` is not currently supported on Snakemake, and thus if you want to download images separately, use the regular interactive or batch program.


**NOTE**

Initially you might need to run the script a couple times to get the packages working. During first times when running you might encounter a warning:

```
WARNING: The scripts f2py, f2py3 and f2py3.6 are installed in '/users/username/.local/bin' which is not on PATH.Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

This might not break the script, or if it does, just re-run and all should be ok.

## A. In case of failures
To ensure that the process flows smoothly, it is recommended to restart the entire program to a blank folder. Thus, if you managed to download something to /your/results/folder/, you should first `rm -r /your/results/folder` to clear the plate. If using snakemake, you don't have to restart but can rather retry with `snakemake --cores 4`, but make sure that scripts/processinglimit.txt is set to 0, or deleted entirely.

## B. How to not delete raw images
Unprocessed images are by default delted after processing due to the large size of the images. It is possible to download the images only once, however, if for example you're working with large timeseries and downloading images takes a considerable amount of time, and want to try different processing parameters. To achieve this, you should:

1. Set deleteUnprocessedImages to False in arguments.csv
2. Run the program using Snakemake
3. After running the script once, go to your results folder, and delete snake_log/images_processed.txt (and timeseries.txt if you want to re-do the timeseries).
4. Change your processing parameters to what you wish
4. Re-run the script with Snakemake. It now starts from processing, and creates a new timeseries. Note that this replaces the old processed images and time series, so if you want to keep them, copy them somewhere else. 
