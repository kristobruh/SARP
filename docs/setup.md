## Setup

### Dependencies
This program is configured for CSC's Puhti environment. As such, it uses modules _geoconda_ and _snap_, along with a few external packages that are installed locally. The packages are:

- fmiopendata
- asf_search
- download_eofs

### 0. Create and verify Eathdata account
You need to have a verified Earthdata account with appropriate permssions in order to download images and orbit files. You can create the account here:
https://asf.alaska.edu/how-to/data-basics/get-started-with-an-earthdata-login-account/

Then verify the account through email.

After doing so, you need to give permissions to ASF to download data. This can be done through here:
https://urs.earthdata.nasa.gov/profile

Sign in to you account, and navigate to **applications --> authorized apps**. Then click APPROVE MORE APPLICATIONS, and write "Alaska Satellite Facility Data Access", and give it permissions.

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

### 1. Clone repository
Use `git clone https://gitlab.com/fgi_nls/kauko/chade/sarp.git` to clone the repository to a destination of your liking.

### 2. Set up input shapefile
You can use `example_target.gpkg` to try out the script, or use your own target. .shp and .gpgk files, as well as coordinate csv's, are accepted as input.

### 3. Configure arguments
In `arguments.txt`,set up your preferred arguments. It is good to start with a short timeframe, e.g. 10 days and `GRD_HD` processing processingLevel and GRD as `process``, to configure the packages. See the file for more descriptions on the parameters. Note: If you use a predefined process, there is no need to define the individual parameters separately. 

For more detailed explanation on download parameters, see: https://docs.asf.alaska.edu/api/keywords/ and https://docs.asf.alaska.edu/asf_search/ASFSearchOptions/.

Initially you might need to run the script a couple times to get the packages working.


### 5a. Run using CLI:
To run, you need to navigate to sarp/scripts/. The basic command is: 

```<run type> <script name> -s <source file> -r <result folder> -b (bulk download) -p (parse input file) ```

Source file path and results folder path are mandatory. Optional commands include:
- Bulk download `-b`: Whether images are downloaded only once. This is useful if the shapefile targets are located close to one another, a thus likely within one approx. 200kmx200km SAR image. If not enabled, each object is downloaded separately.
- Parse shapefile `-p`: Whether polygons in the shapefile are separated to individual objects. If enabled, masking and timeseries is done to the entire shapefile. Usually it is wise to enable this for individual parcel analysis.

**Interactive**

Before running the script in interactive, start a new job by `sinteractive -i`, and set up your parameters. The script is partly parallelized, so several cores is recommended, and at least 12GB of memory.

Example for running interactive: 

`bash run_interactive.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/ -b -p `



**Batch**

`sbatch run_batch.sh -s /path/to/shapefile/folder/ -r /path/to/results/folder/  -b -p`

If you run the script in batch process mode, remember to set up the batch process paramters in `run_batch.sh`. It is recommended to first run it in interactive to ensure that all works.

For some example commands, see **command.txt**.


### 5b. Run using Snakemake:
Again, navigate to sarp/scripts/. Set up the input parameters (source, target directory, bulk processing, separating) in config.yaml found in the folder. After that, in your CLI either write:

`module load snakemake`

`snakemake --cores 4`

for interactive process, or:

`sbatch run_batch_snakemake.sh`

for batch processing. Just remember to configure that batch process file parameters the same way as in regular batch processing.