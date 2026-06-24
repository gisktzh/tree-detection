import os
import sys
import pdal
import json
import glob
from multiprocessing import Pool
from pathlib import Path, PurePath

# Config
# Directories
norm_z_dir = sys.argv[1]
tree_type_raster_dir = sys.argv[2]

# # Pipelines
pipeline_TreeType = sys.argv[3]

# # Further parameters
raster_length = int(sys.argv[4]) # 2017: set to 1000
max_files = int(sys.argv[5]) if sys.argv[5] != "None" else None # cast from str

# Make Output Folders if not existing
if not os.path.exists(tree_type_raster_dir):
    os.makedirs(tree_type_raster_dir)

# Read Pipeline
with open(pipeline_TreeType) as f:
    data = json.load(f)
pipe_TreeType = pdal.Pipeline(json.dumps(data))

# Je nach Jahr können Kacheln nach folgenden Schemata benannt sein:
# 2014:     26885_12380.laz         Länge, Breite: 500 m --> zwei 0 hinzufügen
# 2017:     2690_1251.laz           Länge, Breite: 1000 m --> drei 0 hinzufügen
# 2022:     2678000_1235000.laz     Länge, Breite: 500 m --> so belassen
# Extent wird in Funktionen unten jeweils angepasst.
def uniform_filename(filename):
    if len(filename) == 19:
        return filename

    parts = filename.split("_")
    if len(parts) == 2:
        x = parts[0]
        y = parts[1].split('.')[0]
        suffix = f".{parts[1].split('.')[1]}"

    match len(filename):
        case 15:
            return f"{x}00_{y}00{suffix}"
        case 13:
            return f"{x}000_{y}000{suffix}"


def applyPipelineTreeType(file):
    in_path = PurePath(Path(norm_z_dir),
                        Path(file)).as_posix()
    out_raster_path = PurePath(Path(tree_type_raster_dir),
                               Path(file.replace('.laz', '_TreeType.tif'))).as_posix()
    temp_filename = uniform_filename(file)
    origin_x, origin_y = temp_filename.rstrip('.laz').split('_')

    # überschreibe Reader für das Input File
    Stage_read = json.loads(pipe_TreeType.toJSON())[0]
    Stage_read['filename'] = in_path

    # überschreibe den Writer tif
    Stage_write_tif = json.loads(pipe_TreeType.toJSON())[-1]
    Stage_write_tif['filename'] = out_raster_path
    Stage_write_tif['origin_x'], Stage_write_tif['origin_y'] = origin_x, origin_y
    Stage_write_tif['width'] = raster_length
    Stage_write_tif['height'] = raster_length

    # zusammenfügen
    pipeline = [Stage_read] + json.loads(
        pipe_TreeType.toJSON())[1:5] + [Stage_write_tif]
    d = {}
    d['pipeline'] = pipeline

    pipeline = pdal.Pipeline(json.dumps(d))

    count = pipeline.execute()
    log = pipeline.log
    print(log)


if __name__ == '__main__':

    norm_z_files = [os.path.basename(name) for name in glob.glob(f"{norm_z_dir}/*.laz")]
    print("Job Apply TreeType Pipeline started")
    pool = Pool(processes=8)
    pool.map(applyPipelineTreeType, norm_z_files[:max_files])
    print("All TreeType pipelines done")
