import pandas as pd
import tidy3d.web as web
import os

# --- 1. SETTINGS & DIRECTORY ---
# Use 'r' before the path to handle Windows backslashes correctly
DOWNLOAD_DIR = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_tasks"
EXCEL_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar.xlsx"
ID_COLUMN = "Task ID"

# Create the folder if it doesn't exist yet
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"Created new directory: {DOWNLOAD_DIR}")

# --- 2. LOAD TASK IDs ---
try:
    df = pd.read_excel(EXCEL_FILE)
    task_ids = df[ID_COLUMN].astype(str).str.strip().tolist()
    print(f"Loaded {len(task_ids)} Task IDs from {EXCEL_FILE}")
except Exception as e:
    print(f"Error reading Excel file: {e}")
    task_ids = []

# --- 3. DOWNLOAD LOOP ---
success_count = 0
fail_count = 0

for tid in task_ids:
    # Construct the full path for the local HDF5 file
    hdf5_path = os.path.join(DOWNLOAD_DIR, f"{tid}.hdf5")

    if os.path.exists(hdf5_path):
        print(f"Skipping {tid} (Already exists)")
        success_count += 1
        continue

    try:
        print(f"Downloading {tid}...")
        # Using the specific 'download' method that worked for you
        web.api.webapi.download(task_id=tid, path=hdf5_path)
        success_count += 1
    except Exception as e:
        print(f"Failed to download {tid}: {e}")
        fail_count += 1

# --- 4. SUMMARY ---
print("\n" + "="*40)
print(f"DOWNLOAD COMPLETE")
print(f"Successfully available: {success_count}")
print(f"Failed: {fail_count}")
print(f"Files are located in: {DOWNLOAD_DIR}")
print("="*40)