"""
IMPORTANT: This script has to be run with an ArcPy-compatible Python binary
"""
import os
import sys
import arcpy

# Input data
in_raster = sys.argv[1]

# Output data
out_raster = sys.argv[2]

# Further parameters
extent = sys.argv[3]
cell_size = sys.argv[4]

# Remove inherited environmental variables
for var in ['GDAL_DATA', 'GDAL_DRIVER_PATH']:
    if var in os.environ:
        os.environ.pop(var)

try:
    with arcpy.EnvManager(
        overwriteOutput=True,
        compression="'LZW' 75",
        outputCoordinateSystem='PROJCS["CH1903+_LV95",GEOGCS["GCS_CH1903+",DATUM["D_CH1903+",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator_Azimuth_Center"],PARAMETER["False_Easting",2600000.0],PARAMETER["False_Northing",1200000.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Azimuth",90.0],PARAMETER["Longitude_Of_Center",7.439583333333333],PARAMETER["Latitude_Of_Center",46.95240555555556],UNIT["Meter",1.0]]',
        rasterStatistics="NONE",
        resamplingMethod="BILINEAR",
        pyramid="NONE",
        extent=f'{extent} PROJCS["CH1903+_LV95",GEOGCS["GCS_CH1903+",DATUM["D_CH1903+",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator_Azimuth_Center"],PARAMETER["False_Easting",2600000.0],PARAMETER["False_Northing",1200000.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Azimuth",90.0],PARAMETER["Longitude_Of_Center",7.439583333333333],PARAMETER["Latitude_Of_Center",46.95240555555556],UNIT["Meter",1.0]],VERTCS["LN_1902",VDATUM["Landesnivellement_1902"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]',
        cellSize=cell_size
        ):
        arcpy.management.CopyRaster(
            in_raster=in_raster,
            out_rasterdataset=out_raster,
            config_keyword="",
            background_value=None,
            nodata_value="-3.4028235e+38",
            onebit_to_eightbit="NONE",
            colormap_to_RGB="NONE",
            pixel_type="32_BIT_FLOAT",
            scale_pixel_value="NONE",
            RGB_to_Colormap="NONE",
            format="TIFF",
            transform="NONE",
            process_as_multidimensional="CURRENT_SLICE",
            build_multidimensional_transpose="NO_TRANSPOSE"
        )
    print(f'VHM raster {out_raster} sucessfully written')

except Exception:
    print(arcpy.GetMessages(2))
    raise
