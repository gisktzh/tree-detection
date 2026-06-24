#%%
import sys
import subprocess

# Dir Input
tree_volume_dir = sys.argv[1]
tree_type_dir = sys.argv[2]

# VRT Output
tree_volume_vrt = sys.argv[3]
tree_type_vrt = sys.argv[4]

subprocess.run([
    "gdalbuildvrt",
    tree_volume_vrt,
    tree_volume_dir + r'\*.tif'
])

subprocess.run([
    "gdalbuildvrt",
    tree_type_vrt,
    tree_type_dir + r'\*.tif'
])
