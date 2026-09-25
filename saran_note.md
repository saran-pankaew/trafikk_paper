# Run Bottle-neck

Here I listed the thing that might be missing and some issues I've got in my run.

1. 02_drexpa : No file called `DrugTargetInteractionDB.db` which blocked the run for the Drexpa module
2. 03_gitsbe : 
    - the file `gitsbe_set_folders.py` used the Window path which are not quite compatible with other systems. 
    - The script `run_gitsbe_local.py` has the same problem. It used the Window path and requires a folder setup. I've modified the script so that it declares a relative path (also should be compatible with all systems ?), plus everything becomes automatic.
    - The file `gitsbe-1.3.1-jar-with-dependencies.jar` is missing from the folder. Can't find it in the repo.
3. 04_oris :
   - There is currently no instruction on how to run oris. I'm not quite sure where to start from this. If you have a script for the oris run it would be great.
4. 05_synco :
   - The synco run requires a modele called `zipero.cli` which is actually not a python script. I couldn't find the file, and also it's not on the pypi or conda. So, probably, this will be added to the pipeline afterwards. 
5. 06_siflex :
   - The siflex module is able to compute the results, but there is a problem on aggregating the simulation results. This is caused by specific `numpy` version. To fix this we can fix the file in the `siflex` module itself. 
   - I fixed the file `siflex/apps/network_explorer`. 