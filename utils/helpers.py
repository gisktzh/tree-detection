import os
import subprocess
import sys
import yaml

# YAML constructors
def concat_constructor(loader, node):
    """Recursive YAML list concatenator."""
    return "".join([loader.construct_sequence(val) if isinstance(val, list) else val for val in loader.construct_sequence(node)])


# Load YAML file
def load_config(path: str) -> dict:
    """Read, parse and return config YAML."""
    # Add concat constructor
    yaml.add_constructor(
        "!concat",
        constructor=concat_constructor,
        Loader=yaml.SafeLoader
    )

    # Read YAML
    try:
        with open(file=path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError as e: # Provide custom exception message
        print(f"Error:\t{e}\n--->Make sure to rename the config.sample.yaml file to config.yml and adapt it.")
        sys.exit()

    return config


def flatten_args(args):
    """Flatten input and output arguments and coerce values to string."""
    # Get arguments in the right structure
    args_flat = {}
    for key, val in args.items():
        if key in ("input", "output"):
            for key2, val2 in val.items():
                args_flat[f'{key}.{key2}'] = str(val2)
        else:
            args_flat[key] = str(val)
    return args_flat


# Subprocess definition
def run_subprocess(args):
    """
    Subprocess with live stream of stdout
    """
    args = flatten_args(args)
    print(f'Starting the following subprocess:\n---\n' + "\n".join([f'{k}: {v}' for k, v in args.items()]) + "\n---\n***\n")

    process = subprocess.Popen(
        list(args.values()),
        stdout=subprocess.PIPE, # pipe stdout to main
        stderr=subprocess.STDOUT, # merge stderr into stdout
        text=True,
        bufsize=1 # line-buffered
    )

    # Stream line-by-line
    if process.stdout is not None:
        for line in process.stdout:
            print(line)

    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, args)
    else:
        print(f'Subprocess ended\n---')
