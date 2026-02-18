import h5py
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- 1. CONFIGURATION ---
CACHE_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar.xlsx"
PLOT_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_plots"

# Target Wavelengths
TARGET_WL = [0.795, 0.8, 0.895]

# Paths within HDF5
T_PATH = "data/0/flux/__xarray_dataarray_variable__"
R_PATH = "data/1/flux/__xarray_dataarray_variable__"
FREQ_PATH = "data/0/flux/f" 

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# --- 2. LOAD TASK MAPPING ---
try:
    mapping_df = pd.read_excel(EXCEL_FILE)
    # Ensure Task ID is treated as a string to match filename parsing
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
                t_vals = (np.abs(f[T_PATH][()]) * 100)/2
                r_vals = (np.abs(f[R_PATH][()]) * 100)/2
                
                # Extract values at specific indices
                for i, target in enumerate(TARGET_WL):
                    results_list.append({
                        "Run Name": run_name,
                        "Target Wavelength": target,
                        "Transmission (%)": t_vals[indices[i]],
                        "Reflection (%)": r_vals[indices[i]]
                    })
    except Exception as e:
        print(f"   [!] Error reading {filename}: {e}")

# --- 4. FORMAT RESULTS ---
summary_df = pd.DataFrame(results_list)

# Diagnostic: Check for duplicates that would crash a standard .pivot()
duplicates = summary_df.duplicated(subset=["Run Name", "Target Wavelength"]).any()
if duplicates:
    print("Note: Found duplicate Run Names for the same wavelength. These will be averaged in the plot.")

summary_df.to_csv(os.path.join(PLOT_DIR, "DOE_Target_Summary.csv"), index=False)

# --- 5. PLOTTING TARGET VARIATION ---
def plot_target_comparison(metric):
    plt.figure(figsize=(16, 8), dpi=300)
    plt.title(f"DOE Comparison at Target Wavelengths: {metric}", fontsize=16, fontweight='bold')
    
    # Use pivot_table with aggfunc='mean' to handle duplicate "Run Names"
    plot_df = summary_df.pivot_table(index="Run Name", columns="Target Wavelength", values=metric, aggfunc='mean')
    
    # Plot each target as a different series
    for wl in TARGET_WL:
        # Using fr"" (f-string raw) prevents the \m SyntaxWarning
        plt.scatter(plot_df.index, plot_df[wl], label=fr"at {wl} $\mu m$", s=80, edgecolors='k', alpha=0.7)
    
    plt.ylabel(metric, fontsize=12)
    plt.xlabel("Run Name", fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    
    save_path = os.path.join(PLOT_DIR, f"Target_Comparison_{metric.split()[0]}.png")
    plt.savefig(save_path)
    plt.close() # Free up memory
    print(f"Saved: {save_path}")

# Run plotting functions
if not summary_df.empty:
    plot_target_comparison("Transmission (%)")
    plot_target_comparison("Reflection (%)")
else:
    print("No data extracted. Check your HDF5 file paths or CACHE_DIR.")

print("\n" + "="*40)
print(f"DONE! Target summary CSV and plots created in {PLOT_DIR}")
print("="*40)