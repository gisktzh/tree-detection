import os
import sys
import pdal
import json
import glob
from multiprocessing import Pool
from pathlib import Path, PurePath

# Config
# Directories
laz_dir = sys.argv[1]
norm_z_dir = sys.argv[2]
tree_volume_raster_dir = sys.argv[3]

# Pipelines
pipeline_TreeVolume = sys.argv[4]

# Further parameters
raster_length = int(sys.argv[5]) # 2017: set to 1000
max_files = int(sys.argv[6]) if sys.argv[6] != "None" else None # cast from str

# Make Output Folders if not existing
for folder in [norm_z_dir, tree_volume_raster_dir]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Read Pipeline
with open(pipeline_TreeVolume) as f:
    data = json.load(f)
pipeTreeVolume = pdal.Pipeline(json.dumps(data))

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


def applyPipelineTreeVolume(file):
    input_laz = Path(laz_dir, file).as_posix()
    out_norm_z_path = PurePath(Path(norm_z_dir),
                               Path(file)).as_posix()
    out_raster_path = PurePath(Path(tree_volume_raster_dir),
                               Path(file.replace('.laz', '.tif'))).as_posix()

    # origin_x = 2_600_000
    # origin_y = 1_200_000
    temp_filename = uniform_filename(file) # e.g. for these files "2669_1260.laz",
    origin_x, origin_y = temp_filename.rstrip('.laz').split('_')

    # überschreibe Reader für das Input File
    Stage_read = json.loads(pipeTreeVolume.toJSON())[0]
    Stage_read['filename'] = input_laz

    # überschreibe den Writer las
    Stage_write_las = json.loads(pipeTreeVolume.toJSON())[5]
    Stage_write_las['filename'] = out_norm_z_path

    # überschreibe den Writer tif
    Stage_write_tif = json.loads(pipeTreeVolume.toJSON())[-1]
    Stage_write_tif['filename'] = out_raster_path
    Stage_write_tif['origin_x'], Stage_write_tif['origin_y'] = origin_x, origin_y

    # zusammenfügen
    pipeline = [Stage_read] + json.loads(
        pipeTreeVolume.toJSON())[1:5] + [Stage_write_las] + json.loads(
            pipeTreeVolume.toJSON())[6:7] + [Stage_write_tif]
    d = {}
    d['pipeline'] = pipeline

    pipeline = pdal.Pipeline(json.dumps(d))
    # execute and log
    count = pipeline.execute()
    log = pipeline.log
    print(log)

if __name__ == '__main__':
    laz_files = [os.path.basename(name) for name in glob.glob(f"{laz_dir}/*.laz")]

    print("Job Apply TreeVolume Pipeline started")
    pool = Pool(processes=8)
    pool.map(applyPipelineTreeVolume, laz_files[:max_files])
    print("All TreeVolume pipelines done")
