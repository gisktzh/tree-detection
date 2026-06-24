#%% Setup
import os
import sys
from shutil import copy

# Define Folders
src_dir = sys.argv[1]
dst_dir = sys.argv[2]
max_files = int(sys.argv[3]) if sys.argv[3] != "None" else None # cast from str

if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

laz_files = [f'{path}\\{filename}' for path, _, filenames in os.walk(src_dir) for filename in filenames if filename.endswith(".laz")]

for file in laz_files[:max_files]:
    copy(file, dst_dir)

print(f'{len(laz_files)} point cloud files successfully copied')
