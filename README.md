# Workflow Tree detection


## Description
This code base detects and segments trees in a vegetation/canopy height model.
It is designed as a fully automatic pipeline.

## Process

0. Set Up Environment:
  - Python:
    ```bash
    cd tree-detection
    conda create -f tree-detection/env.yml
    conda activate tree-detection
    ```

Tasks in 1-11 in `./tasks` can be executed using the `./main.py` script. Copy the `sample_config.yaml` to `config_X.yaml`, adapt the settings to your environment and run the file:

1. Prepare Data according to `sample_config.yml`
2. Adapt columns look-up table to your corresponding data model
3. Run [Python](./main.py)
