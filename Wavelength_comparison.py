import h5py
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- 1. CONFIGURATION ---
CACHE_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200.xlsx"
PLOT_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_plots"

# Target Wavelengths
TARGET_WL = [0.795, 0.8, 0.895]

# --- SWAPPED PATHS HERE ---
T_PATH = "data/0/flux/__xarray_dataarray_variable__"
R_PATH = "data/1/flux/__xarray_dataarray_variable__"
FREQ_PATH = "data/0/flux/f" 

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# --- 2. LOAD TASK MAPPING ---
try:
    mapping_df = pd.read_excel(EXCEL_FILE)
    name_mapping = dict(zip(mapping_df["Task ID"].astype(str), mapping_df["Task Name"]))
    print(f"Loaded {len(name_mapping)} task mappings.")
except Exception as e:
    print(f"Error reading Excel: {e}")
    name_mapping = {}

# --- 3. DATA EXTRACTION ---
results_list = []
wavelengths_set = False
indices = []

files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".hdf5")]
print(f"Extracting data at {TARGET_WL} from {len(files)} files...")

for filename in files:
    filepath = os.path.join(CACHE_DIR, filename)
    task_id = filename.replace(".hdf5", "")
    run_name = name_mapping.get(task_id, task_id)
    
    try:
        with h5py.File(filepath, "r") as f:
            if FREQ_PATH in f and not wavelengths_set:
                freqs = f[FREQ_PATH][()]
                wavelengths = 299792458 / freqs * 1e6
                # Find the closest data indices for our targets
                indices = [np.abs(wavelengths - t).argmin() for t in TARGET_WL]
                actual_wl = [wavelengths[i] for i in indices]
                print(f"Mapped targets to actual simulation wavelengths: {np.round(actual_wl, 4)}")
                wavelengths_set = True

            if T_PATH in f and R_PATH in f:
                # Logic remains the same, but the variables T_PATH and R_PATH are now correct
                t_vals = np.abs(f[T_PATH][()]) * 100
                r_vals = np.abs(f[R_PATH][()]) * 100
                
                # Extract values at specific indices
                for i, target in enumerate(TARGET_WL):
                    results_list.append({
                        "Run Name": run_name,
                        "Target Wavelength": target,
                        "Transmission (%)": t_vals[indices[i]],
                        "Reflection (%)": r_vals[indices[i]]
                    })
    except Exception as e:
        print(f"  [!] Error reading {filename}: {e}")

# --- 4. FORMAT RESULTS ---
summary_df = pd.DataFrame(results_list)
summary_df.to_csv(os.path.join(PLOT_DIR, "DOE_Target_Summary.csv"), index=False)

# --- 5. PLOTTING TARGET VARIATION ---
def plot_target_comparison(metric):
    plt.figure(figsize=(16, 8), dpi=300)
    plt.title(f"DOE Comparison at Target Wavelengths: {metric}", fontsize=16, fontweight='bold')
    
    # Pivot for plotting: Rows=Runs, Columns=Wavelengths
    plot_df = summary_df.pivot(index="Run Name", columns="Target Wavelength", values=metric)
    
    # Plot each target as a different series
    for wl in TARGET_WL:
        plt.scatter(plot_df.index, plot_df[wl], label=f"at {wl} $\mu m$", s=80, edgecolors='k', alpha=0.7)
    
    plt.ylabel(metric, fontsize=12)
    plt.xlabel("Run Name", fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    
    save_path = os.path.join(PLOT_DIR, f"Target_Comparison_{metric.split()[0]}.png")
    plt.savefig(save_path)
    print(f"Saved: {save_path}")

plot_target_comparison("Transmission (%)")
plot_target_comparison("Reflection (%)")

print("\n" + "="*40)
print(f"DONE! Target summary CSV and plots created in {PLOT_DIR}")
print("="*40)