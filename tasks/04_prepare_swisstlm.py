#%% Setup
import sys
import zipfile
from osgeo import gdal
import geopandas as gpd

# Input data
swisstlm_zip = sys.argv[1]
clip_geom = sys.argv[2]

# Output data
gpkg_einzelbaum = sys.argv[3]

#%% Read data
# GDFs
gdf_clip = gpd.read_file(clip_geom)

# Extract zip file
with zipfile.ZipFile(swisstlm_zip, 'r') as zip_content:

    # List files in the zip
    zip_files = [file for file in zip_content.namelist()]

    # Check FileGeoDB
    if len(zip_files) != 1:
        if "gdb" in zip_files:
            print("FileGeoDBs are currently not supported, sorry!")
            exit(1)

    # Check GeoPackage
    elif not zip_files[0].endswith(".gpkg"):
        raise Exception(f'Expected only one GeoPackage file in the swissTLM zip file')

    # Load file to memory
    gpkg_bytes = zip_content.read(zip_files[0])
    vsipath = "/vsimem/swisstlm.gpkg"
    gdal.FileFromMemBuffer(vsipath, gpkg_bytes)

    # Find layer name
    search_term = "einzelbaum"
    df_layers = gpd.list_layers(vsipath)
    matches = [layer for layer in df_layers["name"] if search_term in layer.lower()]

    # Make sure that only one layer is found
    if len(matches) != 1:
        raise Exception(f'No unique match was found for "{search_term}". Matching layers: {matches}')

    # I/O layer
    layer = matches[0]
    gdf_tlm = gpd.read_file(vsipath, layer=layer, bbox=tuple(gdf_clip.bounds.values[0]), columns="geom")
    gdf_tlm.clip(gdf_clip.to_crs(gdf_tlm.crs)).to_file(filename=gpkg_einzelbaum)

print(f'Layer "{layer}" successfully read, clipped and written to {gpkg_einzelbaum}')
