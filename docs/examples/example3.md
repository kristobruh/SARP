### Example 3: PolSAR processing in Snakemake, interactive

This example uses the same inputs as example 2, so arguments.txt remains the same. The only change is done to sarp/config.yaml, where the input arguments ae set up:

```
source_path: "/path/to/shapefile/folder/example_target.gpkg"
data_path: "/path/to/results/folder/example"
separate: true
bulk_download: true
restart-times: 3
```

Then, the process is called:

`module load snakemake`

`snakemake --cores 4`.

This then prints out the dependencies and working order, and proceeds to complete them as needed:


```
Assuming unrestricted shared filesystem usage.
Building DAG of jobs...
Using shell: /usr/bin/bash
Provided cores: 4
Rules claiming more threads will be scaled down.
Job stats:
job                     count
--------------------  -------
aggregate_benchmarks        1
all                         1
create_timeseries           1
download_dem                1
download_images             1
download_orbits             1
initialize                  1
process_images              1
total                       8

Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:20:18 2024]
localrule initialize:
    input: initialize.py
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    jobid: 3
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Shapefile processing complete.

[Mon Jul 15 11:20:26 2024]
Finished job 3.
1 of 8 steps (12%) done
Select jobs to execute...
Execute 2 jobs...

[Mon Jul 15 11:20:26 2024]
localrule download_images:
    input: download_images.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt
    jobid: 4
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


[Mon Jul 15 11:20:26 2024]
localrule download_dem:
    input: download_dem.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt
    jobid: 5
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Writing DEM...
DEM saved.

[Mon Jul 15 11:20:31 2024]
Finished job 5.
2 of 8 steps (25%) done
Authenticating...
Searching for results...
Downloading 1 images...
Download complete.
Unzipping...
Unzip done.

[Mon Jul 15 11:24:17 2024]
Finished job 4.
3 of 8 steps (38%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:24:17 2024]
localrule download_orbits:
    input: download_orbits.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt
    jobid: 6
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp


Downloading orbit files...
Orbit files sorted and moved to their respective directories.

[Mon Jul 15 11:24:33 2024]
Finished job 6.
4 of 8 steps (50%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:24:33 2024]
localrule process_images:
    input: process_images_snakemake.py, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    jobid: 2
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/orbits_downloaded.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/initialized.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/dem_downloaded.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

Lock acquired.
        Applying orbit file...

100% done.
Lock released.
        Calibration...

100% done.
        Debursting SLC...

100% done.
        Polarimetric spekle filtering...

100% done.
        Calculating entropy, anisotropy, and alpha...

100% done.
        Calculating Stokes parameters...

100% done.
        Stacking polSAR parameters...

100% done.
        Terrain correction...

100% done.
        Subsetting...

100% done.
Writing...
Processing done.

All tasks completed.
[Mon Jul 15 11:25:29 2024]
Finished job 2.
5 of 8 steps (62%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:25:29 2024]
localrule create_timeseries:
    input: timeseries.py, /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt
    jobid: 1
    benchmark: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/images_processed.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

Data path: /scratch/project_2001106/lake_timeseries/test/
------------------------------------------
Geoconda 3.10.9, GIS libraries for Python
https://docs.csc.fi/apps/geoconda
------------------------------------------
0040110914
Masking done.
Databases created and data saved.
Timeseries done.

0040210843
Masking done.
Data appended to databases.
Timeseries done.

0040424546
Masking done.
Data appended to databases.
Timeseries done.

0040424647
Masking done.
Data appended to databases.
Timeseries done.

0040658154
Masking done.
Data appended to databases.
Timeseries done.

0040762026
Masking done.
Data appended to databases.
Timeseries done.

0040782032
Masking done.
Data appended to databases.
Timeseries done.

0040827704
Masking done.
Data appended to databases.
Timeseries done.

[Mon Jul 15 11:26:06 2024]
Finished job 1.
6 of 8 steps (75%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:26:06 2024]
localrule aggregate_benchmarks:
    input: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt
    output: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    jobid: 7
    reason: Missing output files: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt; Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_initialize.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_dem.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_process_images.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_create_timeseries.benchmark.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_download_orbits.benchmark.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

[Mon Jul 15 11:26:24 2024]
Finished job 7.
7 of 8 steps (88%) done
Select jobs to execute...
Execute 1 jobs...

[Mon Jul 15 11:26:24 2024]
localrule all:
    input: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    jobid: 0
    reason: Input files updated by another job: /scratch/project_2001106/lake_timeseries/test/snake_log/timeseries.txt, /scratch/project_2001106/lake_timeseries/test/snake_log/benchmark_summary.txt
    resources: tmpdir=/run/nvme/job_22326035/tmp

[Mon Jul 15 11:26:24 2024]
Finished job 0.
8 of 8 steps (100%) done
Complete log: .snakemake/log/2024-07-15T112018.437700.snakemake.log

```