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
    
    # Structures
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

    # Circular Polarization (90-deg phase shift)
    pulse_x = td.GaussianPulse(freq0=freq0, fwidth=fwidth, phase=0)
    pulse_y = td.GaussianPulse(freq0=freq0, fwidth=fwidth, phase=np.pi/2)

    gaussian_beam_x = td.GaussianBeam(
        center=(0, 0, source_z), size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, 0),
        source_time=pulse_x, direction="-", waist_radius=WAIST_RADIUS,
        waist_distance=0, pol_angle=0, name="beam_x"
    )

    gaussian_beam_y = td.GaussianBeam(
        center=(0, 0, source_z), size=(STRUCTURE_WIDTH, STRUCTURE_WIDTH, 0),
        source_time=pulse_y, direction="-", waist_radius=WAIST_RADIUS,
        waist_distance=0, pol_angle=np.pi/2, name="beam_y"
    )

    total_z_span = refl_monitor_z + 1.0
    run_time = (total_z_span * N_SI / td.C_0) * 5 
    bspec = td.BoundarySpec(x=td.Boundary.periodic(), y=td.Boundary.periodic(), z=td.Boundary.pml())

    # Monitor size set to 5um x 5um as requested
    monitor_size = (5.0, 5.0, 0)
    
    t_monitor = td.FluxMonitor(
        center=(0, 0, stack_bottom_z), 
        size=monitor_size, 
        freqs=freqs_23, 
        name="T"
    )
    r_monitor = td.FluxMonitor(
        center=(0, 0, refl_monitor_z), 
        size=monitor_size, 
        freqs=freqs_23, 
        name="R"
    )
    
    source_monitor = td.FieldMonitor(center=(0, 0, source_z), size=(0, 0, 0), freqs=freqs_20, name="Source_Normalization")

    z_min, z_max = -1.0, refl_monitor_z + 1.0
    
    return td.Simulation(
        size=(DOMAIN_WIDTH, DOMAIN_WIDTH, z_max - z_min),
        center=(0, 0, (z_max + z_min) / 2),
        boundary_spec=bspec,
        grid_spec=td.GridSpec.auto(wavelength=np.max(lambdas_23)),
        structures=[sin_bot, si_base, sin_top],
        sources=[gaussian_beam_x, gaussian_beam_y],
        monitors=[t_monitor, r_monitor, source_monitor],
        run_time=run_time
    )

# --- 4. PREPARE TASKS ---
folder_name = "Circular_polar_v2"
sims = {}
process_df = doe_df if RUN_ALL else doe_df.head(1)

for idx, row in process_df.iterrows():
    t_top = row['SiN_T'] * TO_UM
    t_bot = row['SiN_B'] * TO_UM
    sim = make_doe_sim(t_top, t_bot)
    task_name = f"Run_{idx}_T{int(row['SiN_T'])}_B{int(row['SiN_B'])}"
    sims[task_name] = sim

# --- 5. SUBMISSION & NORMALIZATION ---
if RUN_ALL:
    batch = web.Batch(simulations=sims, folder_name=folder_name)
    batch_results = batch.run(path_dir=DATA_DIR) 
else:
    test_name = list(sims.keys())[0]
    test_sim = sims[test_name]
    
    job = web.Job(simulation=test_sim, task_name=test_name, folder_name=folder_name)
    sim_data = job.run() 
    
    # --- ALTERNATIVE NORMALIZATION FOR YOUR VERSION ---
    # Many versions of Tidy3D normalize flux results to 1W per source pulse by default.
    # Since we have TWO sources, the total incident power is 2.0.
    total_incident_power = 2.0
    
    # Calculate Normalized Ratios
    # We take the absolute value and divide by 2.0 (the total power of beam_x + beam_y)
    transmission_normalized = np.abs(sim_data['T'].flux) / total_incident_power
    reflection_normalized = np.abs(sim_data['R'].flux) / total_incident_power

    # Plot for verification
    plt.figure(figsize=(8, 5))
    plt.plot(lambdas_23, transmission_normalized, label='Transmission (Normalized)')
    plt.plot(lambdas_23, reflection_normalized, label='Reflection (Normalized)')
    plt.xlabel('Wavelength (um)')
    plt.ylabel('Efficiency (0 to 1)')
    plt.title('Normalized Circular Polarization Result')
    plt.legend()
    plt.grid(True)
    plt.show()

    output_path = os.path.join(DATA_DIR, f"{test_name}.hdf5")
    sim_data.to_hdf5(output_path)
    print(f"\nTask completed. Max Transmission: {np.max(transmission_normalized):.4f}")