# Tidy3d-FDTD-cloud-simulation-automation
This will have all codes related to automation of FDTD simulation as batch executable jobs, as well as extracting data file for analysis.

1. First run job files
   a) If top and bottom SiN thickness and RI is similar use "SiN_Si_SiN_tranmission_job.py" to run the simulation job. Make sure argument RUN_ALL = FALSE is use first to verify design criteria.
   b) If using quarter wavelength rule optimized thickness then run "QWL_optimized_SiN23_Si_SiN1947_transmission_job.py". Make sure argument RUN_ALL = FALSE is use first to verify design criteria.
   c) If changing the source polarization by adding a secondary source, run "QWL_optimized_SiN23_Si_SiN1947_transmission_Circular_polarization_job.py". Make sure argument RUN_ALL = FALSE is use first to verify design criteria. This will also require normalizing the final results, which will be discussed later in this file.

2. Once the job files are ran, make sure the results make sense and start extracting Task IDs. This will be done in two steps:
  a) List the Task IDs in a separate excel spreadsheet on your computer by running "List_TaskIDs.py". This will list all the .hdf5 file IDs that were ran for your specific simulation job. Check if the IDs have been properly extracted.
  b) The 2nd step is to download the .hdf5 task files into your computer. Run "Download_Task_from_Tidy3d.py" on a separate cache folder. Having the data downloaded in a cache folder speeds the next steps when using it for data analysis.

3. Data analysis: Here you can go crazy and do your own analysis as well but these following scripts do some basic plotting.
  a) "Comparison_TaskID_data.py" plots the Tranmsmission vs Simulation Run data.\
  b) "Wavelength_comparison.py" will plot the comparison of different wavelength data at the thickness values of SiN used.
  c) "3D_surface_plot_Transmission_vs_thickness.py" will do an area plot with a visualization of transmission changing for the top and bottom SiN.
