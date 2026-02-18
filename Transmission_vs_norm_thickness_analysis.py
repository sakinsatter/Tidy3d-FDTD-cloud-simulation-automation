import h5py
import numpy as np
import pandas as pd
import os
import re
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
CACHE_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_SiN_var_thickness_v1_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_SiN_var_thickness_v1.xlsx"
PLOT_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_SiN_var_thickness_v1_plots"
TARGET_WL = [0.795, 0.8, 0.895]

T_PATH = "data/0/flux/__xarray_dataarray_variable__"
FREQ_PATH = "data/0/flux/f"

COL_TASK_ID = "Task ID"
COL_TASK_NAME = "Task Name"

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# --- 2. LOAD AND PARSE DATA ---
try:
    df = pd.read_excel(EXCEL_FILE)
    print("--- Data Extraction ---")

    # Parsing SiN_T and SiN_B from Task Name if they aren't separate columns
    # This looks for 'T' followed by numbers and 'B' followed by numbers
    def extract_thickness(name, part):
        match = re.search(fr'{part}(\d+)', str(name))
        return float(match.group(1)) if match else None

    if 'SiN_T' not in df.columns:
        print("Columns SiN_T/B not found. Extracting from Task Name...")
        df['SiN_T'] = df[COL_TASK_NAME].apply(lambda x: extract_thickness(x, 'T'))
        df['SiN_B'] = df[COL_TASK_NAME].apply(lambda x: extract_thickness(x, 'B'))

    # Drop rows where parsing failed
    df = df.dropna(subset=['SiN_T', 'SiN_B'])

    def normalize_doe(series):
        if series.max() == series.min(): return 0
        return 2 * ((series - series.min()) / (series.max() - series.min())) - 1

    df['SiN_T_norm'] = normalize_doe(df['SiN_T'])
    df['SiN_B_norm'] = normalize_doe(df['SiN_B'])
    df['DOE_Index'] = (df['SiN_T_norm'] + df['SiN_B_norm']) / 2
    
    print(f"Parsed {len(df)} runs. Normalization complete.")
except Exception as e:
    print(f"Error: {e}")
    exit()

# --- 3. HDF5 DATA EXTRACTION ---
results = {}
files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".hdf5")]

for filename in files:
    task_id = filename.replace(".hdf5", "")
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        with h5py.File(filepath, "r") as f:
            freqs = f[FREQ_PATH][()]
            wavelengths = 299792458 / freqs * 1e6
            t_vals = np.abs(f[T_PATH][()]) * 100
            results[task_id] = {wl: t_vals[np.abs(wavelengths - wl).argmin()] for wl in TARGET_WL}
    except Exception as e:
        print(f"  [!] Skipping {filename}: {e}")

# Map to DF
for target in TARGET_WL:
    df[f'T_{target}'] = df[COL_TASK_ID].astype(str).map(lambda x: results.get(x, {}).get(target))

# --- 4. PLOTTING ---
plt.figure(figsize=(12, 7), dpi=300)
plot_df = df.dropna(subset=[f'T_{TARGET_WL[0]}']).sort_values('DOE_Index')

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
for i, target in enumerate(TARGET_WL):
    plt.plot(plot_df['DOE_Index'], plot_df[f'T_{target}'], 
             marker='o', markersize=5, label=fr'Wavelength {target} $\mu m$', 
             color=colors[i], linewidth=1.5, alpha=0.8)

plt.title("ARC Transmission: Statistical DOE Sweep", fontsize=14, fontweight='bold')
plt.xlabel("Normalized Thickness Coordinate (-1 = Min, +1 = Max)", fontsize=12)
plt.ylabel("Transmission (%)", fontsize=12)
plt.axvline(0, color='black', linestyle='--', alpha=0.3)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()
plt.tight_layout()

save_path = os.path.join(PLOT_DIR, "Transmission_vs_Normalized_Thickness.png")
plt.savefig(save_path)
print(f"\nSUCCESS: Plot saved to {save_path}")

# Output Top Runs
df['Avg_T'] = df[[f'T_{t}' for t in TARGET_WL]].mean(axis=1)
print("\n--- TOP 3 OPTIMAL THICKNESSES ---")
print(df.sort_values('Avg_T', ascending=False)[['SiN_T', 'SiN_B', 'Avg_T']].head(3))