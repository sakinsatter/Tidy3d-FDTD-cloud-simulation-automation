import pandas as pd
import numpy as np
import re

def run_sigma_analysis(file_path, wavelength=0.895, lsl=90.0):
    """
    Reads DOE data and performs 3-sigma and 6-sigma analysis.
    :param file_path: Path to .csv or .xlsx file
    :param wavelength: The wavelength to analyze (e.g., 0.895)
    :param lsl: Lower Specification Limit for Transmission (default 90%)
    """
    # 1. Load the file
    if file_path.endswith('.csv'):
        df = pd.read_csv(r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_plots\DOE_Target_Summary.csv")
    else:
        df = pd.read_excel(file_path)

    # 2. Extract Top and Bottom SiN from 'Run Name'
    def parse_run(name):
        match = re.search(r'_T(\d+)_B(\d+)', str(name))
        return (int(match.group(1)), int(match.group(2))) if match else (None, None)

    df[['Top_SiN', 'Bottom_SiN']] = df['Run Name'].apply(lambda x: pd.Series(parse_run(x)))

    # 3. Filter for the target wavelength
    data_subset = df[df['Target Wavelength'] == wavelength].copy()
    
    if data_subset.empty:
        print(f"No data found for wavelength {wavelength}")
        return

    # 4. Statistical Calculations
    transmission = data_subset['Transmission (%)']
    mean = transmission.mean()
    std = transmission.std()

    # Sigma Bounds
    sigma3_low, sigma3_high = mean - 3*std, mean + 3*std
    sigma6_low, sigma6_high = mean - 6*std, mean + 6*std

    # Process Capability (Cpk) - How many sigmas fit between mean and spec limit
    cpk = (mean - lsl) / (3 * std)

    # 5. Output Results
    print(f"--- Statistical Analysis for {wavelength} µm ---")
    print(f"Sample Size:    {len(transmission)}")
    print(f"Mean Trans:     {mean:.2f}%")
    print(f"Std Dev (σ):    {std:.2f}%")
    print(f"\n3-Sigma Range:  [{sigma3_low:.2f}% to {sigma3_high:.2f}%]")
    print(f"6-Sigma Range:  [{sigma6_low:.2f}% to {sigma6_high:.2f}%]")
    print(f"\n--- Process Capability (Target > {lsl}%) ---")
    print(f"Cpk Score:      {cpk:.4f}")
    
    if cpk < 1:
        print("Status: Process is not capable. Significant portion of the design space falls below 90%.")
    elif cpk < 1.33:
        print("Status: Marginally capable. Tighten thickness tolerances.")
    else:
        print("Status: Highly capable (Six Sigma levels if Cpk > 2.0).")

# To run the code:
run_sigma_analysis(r"C:\Users\ssatter\Documents\Midnight\ARC_T_SiN_1947_B_SiN_23_var_thickness_750to1200_Circular_polar_plots\DOE_Target_Summary.csv")