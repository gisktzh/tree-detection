#%% Setup
import sys
import os
import json
import numpy as np
import geopandas as gpd
import shapely
import rasterio, rasterio.mask, rasterio.features
import skimage as ski
import scipy.ndimage as ndi


# Input data
IN_PATH_VHM = sys.argv[1]
IN_PATH_MASK = None if sys.argv[2] == "None" else sys.argv[2]
IN_PATH_AOI = sys.argv[3]
IN_PATH_GRID = sys.argv[4]
IN_PATH_SWISSTLM_POINTS = sys.argv[5]

# Output data
OUT_PATH_TREE_POLYGONS = sys.argv[6]

# Further parameters
SMOOTHING_METHOD = sys.argv[7] # gaussian, mean (uniform), None
GAUSSIAN_SIGMA = float(sys.argv[8]) # Gaussian filter sigma value
MEAN_SIZE = json.loads(sys.argv[9]) # Window for mean filter
H_VEG_MIN = float(sys.argv[10]) # Minimal crown height [m above ground]
MIN_DIST_BETWEEN_SEEDS = int(sys.argv[11]) # Minimal distance between two markers

# I/O
DEFAULT_BAND_INDEX = 1

#%% Area of Interest (AoI)
# Grid -> Entire canton divided into multiple cells
grid = gpd.read_file(IN_PATH_GRID)
aoi = gpd.read_file(IN_PATH_AOI)

# Loop over the grid
for idx, cell in grid.iterrows():

#%% Load VHM
    # Import VHM clipped by AoI geometry
    with rasterio.open(IN_PATH_VHM) as src:
        profile = src.profile
        vhm, transform = rasterio.mask.mask(
            src,
            [cell.geometry],
            crop=True,
            indexes=DEFAULT_BAND_INDEX
        )
    vhm[vhm == profile["nodata"]] = 0

    # Update profile to cropped VHM
    profile.update(
        transform=transform,
        height=vhm.shape[0],
        width=vhm.shape[1]
    )

    del transform

#%% Smooth VHM
    match SMOOTHING_METHOD:
        case "gaussian":
            vhm = ski.filters.gaussian(vhm, sigma=GAUSSIAN_SIGMA)
            filter_applied = f'Gaussian, sigma = {GAUSSIAN_SIGMA}'
        case "mean" | "uniform":
            vhm = ndi.vectorized_filter(vhm, function=np.mean, size=MEAN_SIZE)
            filter_applied = f'Uniform (mean), window size = {MEAN_SIZE}'
        case _:
            filter_applied = f'No smoothing applied'
    print(f'Smoothing kernel applied: {filter_applied}')

#%% Create mask
    # Mask of all pixels below height threshold
    mask_trees = np.logical_and(
        vhm >= H_VEG_MIN,
        rasterio.features.geometry_mask(
            geometries=aoi.geometry,
            out_shape=vhm.shape,
            transform=profile["transform"],
            invert=True
        ),
    )

    # Mask of all pixels touching input mask (forest areas)
    if IN_PATH_MASK:
        mask_trees = np.logical_and(
            mask_trees,
            rasterio.features.geometry_mask(
                geometries=gpd.read_file(IN_PATH_MASK).geometry,
                out_shape=vhm.shape,
                transform=profile["transform"]
            )
        )

#%% Markers
    marker_coordinates = ski.feature.peak_local_max( # for entire kt zh: 205-250 minutes
        vhm * mask_trees,
        min_distance=MIN_DIST_BETWEEN_SEEDS
    )

    if len(marker_coordinates) == 0:
        print(f'No markers found for cell {cell.id}, skipping ({idx+1}/{len(grid)})')
        continue

    # Create array using marker coordinates, assign marker id to pixel
    arr_markers = np.zeros_like(vhm, dtype=np.int32)
    arr_markers[tuple(marker_coordinates.T)] = np.arange(1, len(marker_coordinates) + 1)

    del marker_coordinates

#%% Watershed segmentation
    arr_trees = ski.segmentation.watershed( # kt zh: 11 min
        image=-vhm,
        markers=arr_markers,
        mask=mask_trees
    )

    del vhm, arr_markers, mask_trees

#%% Get swissTLM points per watershed region
    gdf_tlm = gpd.read_file(IN_PATH_SWISSTLM_POINTS, mask=cell.geometry, force_2d=True)

    # Rasterize points
    arr_tlm = rasterio.features.geometry_mask(
        geometries=gdf_tlm.geometry,
        out_shape=arr_trees.shape,
        transform=profile["transform"],
        all_touched=True,
        invert=True
    )

    del gdf_tlm

    # Set the value of each point to its corresponding region
    arr_tlm = np.where(arr_tlm, arr_trees, 0)

    # Count the number of times a region's value is found in the points
    label_count = np.unique(arr_tlm, return_counts=True)

    # Get the list of all regions with more than one point in it
    regions_to_segment = [label for label, count in zip(*label_count) if count > 1 and label != 0]

    del label_count

    # Remove all points that don't need further segmentation
    arr_tlm[~np.isin(arr_tlm, regions_to_segment)] = 0

    # Create the markers array, where each marker becomes a unique value above the label with the highest value
    next_label = arr_trees.max() + 1
    last_label = next_label + np.count_nonzero(arr_tlm)
    arr_tlm[arr_tlm != 0] = np.arange(next_label, last_label)

    del next_label, last_label

#%% Segment regions with more than one point using flat watershed
    # Keep only regions with more than one swissTLM point
    mask_tlm = np.isin(arr_trees, regions_to_segment)

    del regions_to_segment

    # Segment using a flat topography
    arr_subregions = ski.segmentation.watershed(
        image=mask_tlm,
        markers=arr_tlm,
        mask=mask_tlm
    )

#%% Combine both watershed arrays
    arr_trees[mask_tlm] = arr_subregions[mask_tlm]

    del arr_subregions, mask_tlm

#%% Output watershed regions as polygons
    # Transform watershed regions (raster) to polygons
    labels, shapes = zip(*[
        (int(label), shapely.geometry.shape(shape))
        for shape, label in rasterio.features.shapes(
            arr_trees,
            transform=profile["transform"]
        )
        if label != 0 # 0 = background
    ])

    # Transform to GeoDataFrame
    gdf_trees = gpd.GeoDataFrame(data={"label": labels, "geometry": shapes}, crs=profile["crs"])

    del arr_trees, labels, shapes

#%% Remove holes in polygons
    mask_holes = gdf_trees.geometry.apply(lambda shape: bool(shape.interiors))
    gdf_trees.loc[mask_holes, "geometry"] = gdf_trees.loc[mask_holes, "geometry"].apply(
        lambda shape: shapely.Polygon(shapely.get_exterior_ring(shape))
    )

#%% Export vector dataset
    layer_name = f'{os.path.splitext(os.path.split(OUT_PATH_TREE_POLYGONS)[-1])[0]}_{cell.id}'
    gdf_trees.to_file(OUT_PATH_TREE_POLYGONS, layer=layer_name)
    print(f'Successfully exported detected trees for cell {cell.id} ({idx+1}/{len(grid)})')
