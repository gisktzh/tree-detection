"""
Runetime script for the whole pipeline
"""
#%% Setup
from utils.helpers import load_config, run_subprocess

# Load config file
config = load_config("./configs/config_control.yml")

# Prepare VHM (Vegetation Height Model)
run_subprocess(config["vhm"])

# Prepare Area of Interest (Kt ZH)
run_subprocess(config["aoi"])

# Prepare Mask (Waldareal)
run_subprocess(config["mask"])

# Prepare swissTLM (Einzelbäume)
run_subprocess(config["swisstlm"])

# Copy Point Clouds (OPTIONAL)
run_subprocess(config["point_cloud"])

# Run Tree Detection
run_subprocess(config["detect_trees"])

# Run PDAL TreeVolume pipelines
run_subprocess(config["tree_vol_raster"])

# Run PDAL TreeType pipeline
run_subprocess(config["tree_type_raster"])

# Create VRTs
run_subprocess(config["vrt"])

# Calculate Zonal Statistics (height, volume, tree type)
run_subprocess(config["calculate_zonal_stats"])

# Combine, clean and enrich the data into a final dataset
run_subprocess(config["combine_and_postprocess"])

print("We are done here! :-)")
