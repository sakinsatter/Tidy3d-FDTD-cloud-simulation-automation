import h5py
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # Added for tick control

# --- 1. CONFIGURATION (CORRECTED) ---
CACHE_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar.xlsx"
PLOT_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_plots"

# Path indices for HDF5
T_PATH = "data/0/flux/__xarray_dataarray_variable__"
R_PATH = "data/1/flux/__xarray_dataarray_variable__"
FREQ_PATH = "data/0/flux/f"

# --- 2. INITIALIZE DIRECTORIES ---
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)
    print(f"Created plot directory: {PLOT_DIR}")

# --- 3. LOAD TASK MAPPING ---
try:
    mapping_df = pd.read_excel(EXCEL_FILE)
    name_mapping = dict(zip(mapping_df["Task ID"].astype(str), mapping_df["Task Name"]))
    print(f"Loaded {len(name_mapping)} task name mappings.")
except Exception as e:
    print(f"Error reading Excel: {e}")
    name_mapping = {}

# --- 4. PREPARE STORAGE ---
t_data = {}
r_data = {}
wavelengths_set = False

# --- 5. EXTRACTION LOOP ---
files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".hdf5")]
print(f"Processing {len(files)} files...")

for filename in files:
    filepath = os.path.join(CACHE_DIR, filename)
    task_id = filename.replace(".hdf5", "")
    column_name = name_mapping.get(task_id, task_id)
    
    try:
        with h5py.File(filepath, "r") as f:
            # --- MODIFIED: Normalized by 2 ---
            if T_PATH in f:
                # Original: np.abs(f[T_PATH][()]) * 100
                t_data[column_name] = (np.abs(f[T_PATH][()]) * 100) / 2
            if R_PATH in f:
                # Original: np.abs(f[R_PATH][()]) * 100
                r_data[column_name] = (np.abs(f[R_PATH][()]) * 100) / 2
                
            if not wavelengths_set and FREQ_PATH in f:
                freqs = f[FREQ_PATH][()]
                wavelengths = 299792458 / freqs * 1e6
                t_data["Wavelength_um"] = wavelengths
                r_data["Wavelength_um"] = wavelengths
                wavelengths_set = True
    except Exception as e:
        print(f"  [!] Error reading {filename}: {e}")

# --- 6. PLOTTING FUNCTION ---
def save_doe_plot(data_dict, title, filename, ylabel):
    if not data_dict:
        print(f"No data found for {title}. Skipping plot.")
        return
        
    df = pd.DataFrame(data_dict)
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300) 
    plt.title(title, fontsize=16, fontweight='bold')
    
    x = df["Wavelength_um"]
    for col in df.columns:
        if col != "Wavelength_um":
            ax.plot(x, df[col], alpha=0.5, linewidth=1, label=col)
            
    plt.xlabel(r"Wavelength ($\mu m$)", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    
    # X-AXIS SCALE
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.005))
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Legend
    plt.legend(fontsize='7', loc='upper left', bbox_to_anchor=(1, 1), ncol=2)
    
    full_save_path = os.path.join(PLOT_DIR, filename)
    plt.tight_layout()
    plt.savefig(full_save_path)
    print(f"Saved: {full_save_path}")
    plt.close()

# --- 7. EXECUTE ---
# Updated labels to indicate normalization
save_doe_plot(t_data, "DOE Comparison: Transmission (Normalized by 2)", "Transmission_Full_DOE.png", "Transmission (%) / 2")
save_doe_plot(r_data, "DOE Comparison: Reflection (Normalized by 2)", "Reflection_Full_DOE.png", "Reflection (%) / 2")

print("\n" + "="*40)
print(f"ANALYSIS COMPLETE")
print(f"All plots are in: {PLOT_DIR}")
print("="*40)