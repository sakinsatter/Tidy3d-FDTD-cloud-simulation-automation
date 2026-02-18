import h5py
import numpy as np
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. CONFIGURATION ---
CACHE_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200.xlsx"
PLOT_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_plots"
TARGET_WLs = [0.795, 0.8, 0.895]

T_PATH = "data/0/flux/__xarray_dataarray_variable__"
FREQ_PATH = "data/0/flux/f"

COL_TASK_ID = "Task ID"
COL_TASK_NAME = "Task Name"

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# --- 2. DATA LOADING & THICKNESS EXTRACTION ---
df = pd.read_excel(EXCEL_FILE)

def extract_thickness(name, part):
    match = re.search(fr'{part}(\d+)', str(name))
    return float(match.group(1)) if match else None

if 'SiN_T' not in df.columns:
    df['SiN_T'] = df[COL_TASK_NAME].apply(lambda x: extract_thickness(x, 'T'))
    df['SiN_B'] = df[COL_TASK_NAME].apply(lambda x: extract_thickness(x, 'B'))

# --- 3. HDF5 EXTRACTION ---
results = {wl: {} for wl in TARGET_WLs}
files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".hdf5")]

for filename in files:
    task_id = filename.replace(".hdf5", "")
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        with h5py.File(filepath, "r") as f:
            freqs = f[FREQ_PATH][()]
            wavelengths = 299792458 / freqs * 1e6
            t_vals = np.abs(f[T_PATH][()]) * 100
            for wl in TARGET_WLs:
                idx = np.abs(wavelengths - wl).argmin()
                results[wl][task_id] = t_vals[idx]
    except Exception:
        continue

# --- 4. STATIC PLOTTING (MATPLOTLIB) ---
fig_static = plt.figure(figsize=(22, 8), dpi=300)

for i, wl in enumerate(TARGET_WLs):
    temp_df = df.copy()
    temp_df['Transmission'] = temp_df[COL_TASK_ID].astype(str).map(results[wl])
    temp_df = temp_df.dropna(subset=['SiN_T', 'SiN_B', 'Transmission'])

    ax = fig_static.add_subplot(1, 3, i+1, projection='3d')
    xi = np.linspace(temp_df['SiN_T'].min(), temp_df['SiN_T'].max(), 100)
    yi = np.linspace(temp_df['SiN_B'].min(), temp_df['SiN_B'].max(), 100)
    X, Y = np.meshgrid(xi, yi)
    Z = griddata((temp_df['SiN_T'], temp_df['SiN_B']), temp_df['Transmission'], (X, Y), method='cubic')

    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.8)
    ax.scatter(temp_df['SiN_T'], temp_df['SiN_B'], temp_df['Transmission'], color='red', s=15)

    ax.set_title(fr"Transmission (%) at {wl} $\mu m$", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(r"Top SiN ($\AA$)", fontsize=11, labelpad=10)
    ax.set_ylabel(r"Bottom SiN ($\AA$)", fontsize=11, labelpad=10)
    ax.set_zlabel("T (%)", fontsize=11, labelpad=10)
    ax.view_init(elev=28, azim=135)
    fig_static.colorbar(surf, ax=ax, shrink=0.5, aspect=12, pad=0.1)

plt.subplots_adjust(left=0.05, right=0.95, wspace=0.3)
static_save_path = os.path.join(PLOT_DIR, "3D_Surface_Multi_Wavelength_ARC_SiN_1_947.png")
plt.savefig(static_save_path, bbox_inches='tight')
print(f"Static image saved: {static_save_path}")

# --- 5. INTERACTIVE PLOTTING (PLOTLY) ---
fig_interactive = make_subplots(
    rows=1, cols=3,
    specs=[[{'type': 'surface'}, {'type': 'surface'}, {'type': 'surface'}]],
    subplot_titles=[f"Transmission at {wl} µm" for wl in TARGET_WLs]
)

for i, wl in enumerate(TARGET_WLs):
    temp_df = df.copy()
    temp_df['Transmission'] = temp_df[COL_TASK_ID].astype(str).map(results[wl])
    temp_df = temp_df.dropna(subset=['SiN_T', 'SiN_B', 'Transmission'])

    xi = np.linspace(temp_df['SiN_T'].min(), temp_df['SiN_T'].max(), 50)
    yi = np.linspace(temp_df['SiN_B'].min(), temp_df['SiN_B'].max(), 50)
    X, Y = np.meshgrid(xi, yi)
    Z = griddata((temp_df['SiN_T'], temp_df['SiN_B']), temp_df['Transmission'], (X, Y), method='linear')

    # Add Surface
    fig_interactive.add_trace(
        go.Surface(z=Z, x=xi, y=yi, colorscale='Viridis', showscale=(i == 2), name=f"{wl}µm"),
        row=1, col=i+1
    )
    # Add Scatter Points
    fig_interactive.add_trace(
        go.Scatter3d(x=temp_df['SiN_T'], y=temp_df['SiN_B'], z=temp_df['Transmission'],
                     mode='markers', marker=dict(size=4, color='red'), name=f"Points {wl}µm"),
        row=1, col=i+1
    )

fig_interactive.update_layout(
    title="Interactive ARC Transmission DOE Analysis",
    height=800, width=1800,
    margin=dict(l=50, r=50, b=50, t=100)
)

interactive_save_path = os.path.join(PLOT_DIR, "3D_Interactive_Surface_ARC_SiN_1_947.html")
fig_interactive.write_html(interactive_save_path)
print(f"Interactive HTML saved: {interactive_save_path}")

plt.show()