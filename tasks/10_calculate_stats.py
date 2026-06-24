#%%
import os
import sys
import subprocess
import geopandas as gpd
import pandas as pd

# Input data
IN_PATH_TREES = sys.argv[1]
IN_PATH_VHM = sys.argv[2]
IN_PATH_VOXEL = sys.argv[3]
IN_PATH_TREE_TYPE = sys.argv[4]

# Output data
OUT_PATH_HEIGHTS = sys.argv[5]
OUT_PATH_VOLUME = sys.argv[6]
OUT_PATH_TREE_TYPE = sys.argv[7]

base_name = f'{os.path.splitext(os.path.split(IN_PATH_TREES)[-1])[0]}'
layers = [(int(layer.split(base_name + "_")[1]), layer) for layer in gpd.list_layers(IN_PATH_TREES)["name"]]

for i, layer in layers:
    # Step 1: Calculate zonal statistics per grid cell
    height_csv = f'_{i}'.join(os.path.splitext(OUT_PATH_HEIGHTS))
    volume_csv = f'_{i}'.join(os.path.splitext(OUT_PATH_VOLUME))
    tree_type_csv = f'_{i}'.join(os.path.splitext(OUT_PATH_TREE_TYPE))

    # Height (VHM)
    gdal_command = " ".join([
        "gdal pipeline",
        f'! read {IN_PATH_VHM}',
        f'! zonal-stats --zones {IN_PATH_TREES} --zones-layer {layer} --include-field label --stat max --stat mean ',
        f'! write {height_csv} --overwrite'
    ])
    subprocess.run(gdal_command)

    # Volume (voxel count)
    gdal_command = " ".join([
        "gdal pipeline",
        f'! read {IN_PATH_VOXEL}',
        f'! zonal-stats --zones {IN_PATH_TREES} --zones-layer {layer} --include-field label --stat sum',
        f'! write {volume_csv} --overwrite'
    ])
    subprocess.run(gdal_command)

    # Tree type (repetition distance)
    gdal_command = " ".join([
        "gdal pipeline",
        f'! read {IN_PATH_TREE_TYPE}',
        f'! zonal-stats --zones {IN_PATH_TREES} --zones-layer {layer} --include-field label --stat mean',
        f'! write {tree_type_csv} --overwrite'
    ])
    subprocess.run(gdal_command)

    # Step 2: Join gpkg back to original gpkg
    gdf = gpd.read_file(IN_PATH_TREES, layer=layer)
    df = pd.read_csv(height_csv
    ).merge(
        pd.read_csv(volume_csv), on="label"
    ).merge(
        pd.read_csv(tree_type_csv), on="label"
    )
    df.columns = ["label", "height_max", "height_mean", "volume", "tree_type_stat"]
    gdf = gdf.merge(df, on='label')

    # Step 3: Normalize by height and save file
    gdf['tree_type_stat'] = gdf['tree_type_stat'] / gdf['height_max']
    gdf.to_file("_stats".join(os.path.splitext(IN_PATH_TREES)), layer=layer)
    print(f'Successfully exported zonal statistics for cell {i}')
