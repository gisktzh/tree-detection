#%%
import sys
import geopandas as gpd
import pandas as pd
import numpy as np

# Input data
IN_GPKG = sys.argv[1]
PATH_FOREST = sys.argv[2]
PATH_TLM = sys.argv[3]

# Output data
OUT_GPKG = sys.argv[4]

AREA_MIN = float(sys.argv[5]) # CRS units (LV95: meters)
H_MAX = float(sys.argv[6])
FLOAT_ROUND_PRECISION = int(sys.argv[5])

# Colum rename look-up table
COL_LUT = {
    "id": "id",
    "height_max": "hoehe_max",
    "height_mean": "hoehe_mittel",
    "area": "kronenflaeche",
    "volume": "baumvol",
    "tree_type_stat": "laubwerfend_stat",
    "centroid_e": "centroid_e",
    "centroid_n": "centroid_n",
    "in_tlm": "in_tlm",
    "tlm_eb_e": "tlm_eb_e",
    "tlm_eb_n": "tlm_eb_n"
}

#%% Combine layers
# Load layers
layers = [
    gpd.read_file(IN_GPKG, layer=layer)
    for layer in gpd.list_layers(IN_GPKG)["name"]
]

# Combine layers
gdf = pd.concat(layers).reset_index()
del layers

# Clean combined data
gdf.drop(["index", "label"], axis=1, inplace=True)
gdf["id"] = gdf.index + 1

#%% Load more data
tlm = gpd.read_file(PATH_TLM)
forest = gpd.read_file(PATH_FOREST)

#%% Clean-up
# Filter small crown areas
gdf = gdf[gdf.area >= AREA_MIN]

# Filter to maximum tree height
gdf = gdf[gdf["height_max"] <= H_MAX]

# Filter trees with volume < area
gdf = gdf[gdf["volume"] >= gdf.area]

# Filter trees intersecting mask geometries (forest areas)
cols = list(gdf.columns)
gdf = gdf.sjoin(forest, "left", "intersects").drop_duplicates("id")
gdf = gdf.loc[gdf["index_right"].isna(), cols]

# Round statistics
gdf["height_max"] = gdf["height_max"].round(FLOAT_ROUND_PRECISION)
gdf["height_mean"] = gdf["height_mean"].round(FLOAT_ROUND_PRECISION)
gdf["tree_type_stat"] = gdf["tree_type_stat"].round(FLOAT_ROUND_PRECISION)

#%% Data enrichment
# Generate centroids
if "centroid_n" not in gdf.columns or "centroid_e" not in gdf.columns:
    gdf["centroid_e"], gdf["centroid_n"] = zip(*gdf.centroid.apply(lambda x: (x.x, x.y)))

# Check centroids
centroid_outside = gdf[~gdf.geometry.contains(gdf.centroid)]
print(f'Number of centroids outside the polygon: {len(centroid_outside)}')

# Calculate crown area
gdf["area"] = gdf.area.astype(np.int32)

cols = list(gdf.columns)
# Keep only one of duplicated features (some have more than one TLM point (bug caused by filling holes after look-up) and thus get duplicated)
gdf = gdf.sjoin(tlm, "left", "intersects").drop_duplicates("id")

# Get coordinates of the corresponding swissTLM point
filter = gdf["index_right"].notna()
gdf.loc[filter, "tlm_eb_e"] = tlm.loc[gdf.loc[filter, "index_right"], "geometry"].x.values
gdf.loc[filter, "tlm_eb_n"] = tlm.loc[gdf.loc[filter, "index_right"], "geometry"].y.values

# Rename index_right to in_tlm and transform to boolean
gdf.rename(columns={"index_right": "in_tlm"}, inplace=True)
gdf["in_tlm"] = gdf["in_tlm"].notna()

gdf = gdf.loc[:, cols + ["in_tlm", "tlm_eb_e", "tlm_eb_n"]]

#%% Impose data model
# Rename columns
col_names = list(gdf.columns)
for i, col in enumerate(gdf.columns):
    for name_old, name_new in COL_LUT.items():
        if col == name_old:
            col_names[i] = name_new
gdf.columns = col_names

gdf = gdf.loc[:, list(COL_LUT.values()) + ["geometry"]]

#%% Export final dataset
gdf.to_file(OUT_GPKG)
