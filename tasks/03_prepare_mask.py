#%% Setup
import sys
import geopandas as gpd

# Input data
wfs_waldareal = sys.argv[1]

# Output data
gpkg_waldareal = sys.argv[2]

#%% I/O data
gdf_waldareal = gpd.read_file(wfs_waldareal).to_file(filename=gpkg_waldareal)
print(f'Mask {gpkg_waldareal} successfully written')
