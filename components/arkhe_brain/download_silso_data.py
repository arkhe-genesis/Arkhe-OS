"""
SILSO Data Downloader for Arkhe-Brain
Downloads monthly sunspot data from the Royal Observatory of Belgium.
"""

import urllib.request
import pandas as pd
import numpy as np
import os

URL = "https://www.sidc.be/silso/INFO/sndtotcsv.php"

def download_silso_data(filepath="SN_d_tot_V2.0.csv"):
    if os.path.exists(filepath):
        print(f"✅ Data already exists at {filepath}")
    else:
        print(f"📥 Downloading SILSO data from {URL}...")
        try:
            urllib.request.urlretrieve(URL, filepath)
            print("✅ Download complete.")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None, None

    try:
        # Format: Year, Month, Day, DecimalYear, SunspotNumber, StdDev, Observations, Status
        df = pd.read_csv(filepath, sep=';', header=None,
                          names=['Year', 'Month', 'Day', 'DecimalYear', 'SunspotNumber', 'StdDev', 'Observations', 'Status'],
                          na_values=['', ' ', '-1'])

        # Filter valid entries
        df = df[df['SunspotNumber'] >= 0]

        years = df['DecimalYear'].values
        sunspots = df['SunspotNumber'].values

        return years, sunspots
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return None, None

if __name__ == "__main__":
    years, sunspots = download_silso_data()
    if years is not None:
        print(f"📊 Data loaded: {len(years)} records ({years.min():.1f} - {years.max():.1f})")
        np.savez('silso_sunspots.npz', years=years, sunspots=sunspots)
