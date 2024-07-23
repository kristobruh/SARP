## Troubleshooting
<br>

**Q:** I get an error when trying to authenticate my account?

**A:** There could be an error in the file creation format. Ensure that the file structure follows the exact formatting.

 <br><br><br>


**Q:** I can't download images, I get lots of Java code printed?

**A:** Check whether your account is verified, and you have given Alaska Satellite Facility the permissions to use your account.

 <br><br><br>


**Q:**  In SNAP processing phase I get an infinite error row in Java?

**A:** The images being written are too large for SNAP to handle. Try to go to scripts/snap_process.py row 12, and reduce processingLimit by one. Three is the maximum that I recommend.

 <br><br><br>


**Q:** My program failed, and when I restarted it doesn't restart the processing phase?

**A:** Try deleting processinglimit.txt from scripts/, it likely reached it's peak when crashing and now it thinks the pipeline is full.


 <br><br><br>

**Q:** I get this error in Snakemake: LockException:
Error: Directory cannot be locked. Please make sure that no other Snakemake process is trying to create the same files in the following directory:
/scratch/project_2001106/lake_timeseries/sarp/scripts
If you are sure that no other instances of snakemake are running on this directory, the remaining lock was likely caused by a kill signal or a power loss. It can be removed with the --unlock argument.


**A**: Write `snakemake --unlock`, this unlocks the process and allows you to try again.


 <br><br><br>


**Q**: I get error: "[Fatal Error] S1A_OPER_AUX_POEORB_OPOD_20230706T080750_V20230615T225942_20230617T005942.EOF:75856:39: XML document structures must start and end within the same entity." when processing?

**A**: There was likely a failure in fully downloading the orbit files. If you want orbit files applied, you need to download the raw images again and process the images again. Otherwise you can ignore it.