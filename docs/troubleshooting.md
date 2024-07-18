## Troubleshooting

**Q:** I get an error when trying to authenticate my account?

**A:** There could be an error in the file creation format. Ensure that the file structure follows the exact formatting.




**Q:** I can't download images, I get lots of Java code printed?

**A:** Check whether your account is verified, and you have given Alaska Satellite Facility the permissions to use your account.




**Q:**  In SNAP processing phase I get an infinite error row in Java?

**A:** You have likely allocated too little memory in the job, or the images being written are too large to handle. Try to first run a new process with new memory, or if that doesn't work, go to scripts/snap_process.py row 12, and reduce processinLimit, or the maximum number or concurrent processes.




**Q:** My program failed, and when I restarted it doesn't restart the processing phase?

**A:** Try deleting processinglimit.txt from scripts/, it likely reached it's peak when crashing and now it thinks the pipeline is full.