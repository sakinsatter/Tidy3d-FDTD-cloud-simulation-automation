import tidy3d.web as web
import pandas as pd
import os

# --- 1. CONFIGURATION ---
FOLDER_NAME = "Circular_polar_v2"
OUTPUT_FILE = r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar.xlsx"

print(f"Connecting to Tidy3D folder: {FOLDER_NAME}...")

try:
    # --- 2. FETCH ALL TASKS IN FOLDER ---
    # This retrieves a list of dictionaries containing metadata for every run
    tasks = web.get_tasks(folder=FOLDER_NAME)
    
    if not tasks:
        print(f"No tasks found in folder '{FOLDER_NAME}'.")
    else:
        # --- 3. EXTRACT RELEVANT DATA ---
        task_data = []
        for t in tasks:
            task_data.append({
                "Task Name": t.get('taskName') or t.get('task_name'),
                "Task ID": t.get('taskId') or t.get('task_id'),
                "Status": t.get('status'),
                "Created": t.get('created')
            })
        
        # --- 4. CREATE DATAFRAME AND SAVE ---
        df = pd.DataFrame(task_data)
        
        # Clean up the Task ID column to ensure no hidden spaces
        df["Task ID"] = df["Task ID"].str.strip()
        
        # Save to Excel
        df.to_excel(OUTPUT_FILE, index=False)
        
        print("\n" + "="*40)
        print(f"SUCCESS! Created {OUTPUT_FILE}")
        print(f"Total tasks found: {len(df)}")
        print("="*40)

except Exception as e:
    print(f"\n[!] ERROR: {e}")
    print("Ensure you are logged in by running 'tidy3d configure' in your terminal.")