import tidy3d as td
import tidy3d.web as web
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
RUN_ALL = True 
DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- 1. LOAD DOE FROM EXCEL ---
doe_df = pd.read_excel(r"C:\Users\ssatter\Documents\Midnight\QWL_optimized_SiN_thickness_DOE.xlsx")
TO_UM = 1e-4 

# --- 2. PARAMETERS & PHYSICS SETUP ---
N_SIN_TOP = 1.947  
N_SIN_BOT = 2.3    
N_SI = 3.7
SI_THICKNESS = 5.0      
WAIST_RADIUS = 1.0      
STRUCTURE_WIDTH = 5.0   
DOMAIN_WIDTH = 8.0      

lambdas_23 = np.linspace(0.79, 0.9, 23)
freqs_23 = td.C_0 / lambdas_23
lambdas_20 = np.linspace(0.79, 0.9, 20)
freqs_20 = td.C_0 / lambdas_20

freq0 = np.mean(freqs_23)
fwidth = (np.max(freqs_23) - np.min(freqs_23)) / 2.0

# --- 3. SIMULATION CONSTRUCTOR ---
def make_doe_sim(t_top_um, t_bot_um):
    mat_si = td.Medium(permittivity=N_SI**2)
    mat_sin_top = td.Medium(permittivity=N_SIN_TOP**2)
    mat_sin_bot = td.Medium(permittivity=N_SIN_BOT**2)
    
    stack_bottom_z = 0.0
    
    sin_bot = td.Structure(
        geometry=td.Box(size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, t_bot_um), 
                        center=(0, 0, t_bot_um / 2)),
        medium=mat_sin_bot, name="SiN Bottom"
    )

    si_base = td.Structure(
        geometry=td.Box(size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, SI_THICKNESS), 
                        center=(0, 0, t_bot_um + SI_THICKNESS / 2)),
        medium=mat_si, name="Si Substrate"
    )
    
    z_top_layer_bot = t_bot_um + SI_THICKNESS
    sin_top = td.Structure(
        geometry=td.Box(size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, t_top_um), 
                        center=(0, 0, z_top_layer_bot + t_top_um / 2)),
        medium=mat_sin_top, name="SiN Top"
    )

    top_of_stack = z_top_layer_bot + t_top_um
    source_z = top_of_stack + 1.5
    refl_monitor_z = source_z + 0.5 

    pulse = td.GaussianPulse(freq0=freq0, fwidth=fwidth)
    gaussian_beam = td.GaussianBeam(
        center=(0, 0, source_z), size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, 0),
        source_time=pulse, direction="-", waist_radius=WAIST_RADIUS,
        waist_distance=0, pol_angle=0
    )

    total_z_span = refl_monitor_z + 1.0
    run_time = (total_z_span * N_SI / td.C_0) * 5 
    bspec = td.BoundarySpec(x=td.Boundary.periodic(), y=td.Boundary.periodic(), z=td.Boundary.pml())

    t_monitor = td.FluxMonitor(center=(0, 0, stack_bottom_z), size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, 0), freqs=freqs_23, name="T")
    r_monitor = td.FluxMonitor(center=(0, 0, refl_monitor_z), size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, 0), freqs=freqs_23, name="R")
    source_monitor = td.FieldMonitor(center=(0, 0, source_z), size=(0, 0, 0), freqs=freqs_20, name="Source_Normalization")

    z_min, z_max = -1.0, refl_monitor_z + 1.0
    
    return td.Simulation(
        size=(DOMAIN_WIDTH, DOMAIN_WIDTH, z_max - z_min),
        center=(0, 0, (z_max + z_min) / 2),
        boundary_spec=bspec,
        grid_spec=td.GridSpec.auto(wavelength=np.max(lambdas_23)),
        structures=[sin_bot, si_base, sin_top],
        sources=[gaussian_beam],
        monitors=[t_monitor, r_monitor, source_monitor],
        run_time=run_time
    )

# --- 4. PREPARE TASKS ---
folder_name = "ARC_SiN_Multi_Index_DOE"
sims = {}
process_df = doe_df if RUN_ALL else doe_df.head(1)

for idx, row in process_df.iterrows():
    t_top = row['SiN_T'] * TO_UM
    t_bot = row['SiN_B'] * TO_UM
    sim = make_doe_sim(t_top, t_bot)
    task_name = f"Run_{idx}_T{int(row['SiN_T'])}_B{int(row['SiN_B'])}"
    sims[task_name] = sim

# --- 5. SUBMISSION ---
if RUN_ALL:
    batch = web.Batch(simulations=sims, folder_name=folder_name)
    # Batch still uses path_dir to download all results at once
    batch_results = batch.run(path_dir=DATA_DIR) 
    print("\nBatch processing complete.")
else:
    test_name = list(sims.keys())[0]
    test_sim = sims[test_name]
    
    print(f"Plotting geometry for: {test_name}...")
    fig, ax = plt.subplots(1, 1, figsize=(6, 8))
    test_sim.plot(y=0, ax=ax)
    plt.show() # Inspect the layers here!

    print(f"Running single test simulation: {test_name}...")
    job = web.Job(simulation=test_sim, task_name=test_name, folder_name=folder_name)
    
    # job.run() for a single Job takes no arguments in many Tidy3D versions
    sim_data = job.run() 
    
    # Explicitly save the data to your local folder
    output_path = os.path.join(DATA_DIR, f"{test_name}.hdf5")
    sim_data.to_hdf5(output_path)
    print(f"\nTest task '{test_name}' completed and saved to {output_path}.")