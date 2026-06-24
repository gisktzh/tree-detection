#%% Setup
import os
import sys
import geopandas as gpd
import numpy as np
import shapely

# Input data
in_aoi = sys.argv[1]

# Output data
out_aoi = sys.argv[2]
out_grid = sys.argv[3]

# Further parameters
where_filter = sys.argv[4]
wkt_grid_bb = [sys.argv[5]]

if where_filter == "None": where_filter = ""

#%% Read data
gdf_kt = gpd.read_file(in_aoi, where=where_filter)
print(f'Reading Area of Interest from {in_aoi}')

#%% Output
# Area of Interest
gdf_kt.to_file(filename=out_aoi)
print(f'Area of Interest {out_aoi} sucessfully written')

#%% Grid
gs_grid_bb = gpd.GeoSeries.from_wkt(wkt_grid_bb, crs=gdf_kt.crs)

minx, miny, maxx, maxy = gs_grid_bb.bounds.values[0]
cell_length = (maxx - minx) / 4

# Build grid cells (polygons)
polys = []

for x0 in np.arange(minx, maxx, cell_length):
    x1 = min(x0 + cell_length, maxx)
    for y0 in np.arange(maxy - cell_length, miny - cell_length, -cell_length):
        y1 = min(y0 + cell_length, maxy)
        polys.append(shapely.geometry.box(x0, y0, x1, y1))

grid = gpd.GeoDataFrame(
    {"id": range(1, len(polys) + 1)},
    geometry=polys,
    crs=gdf_kt.crs
)

grid.to_file(filename=out_grid)
print(f'Grid {out_grid} sucessfully written')
