# pkl model converter

This directory is a simple converter for the pkl models into a standard ONNX + JSON
sidecar workflow.

This was built as the pkl files pin our allowable python and dependencies to EOL
versions.

This only needs to be run once, but serves as documentation for how our models were
update into the ONNX workflow.

## Usage

First run:

`docker build -t model-converter .` within this directory to build the converter

Then run:

`docker run --rm -v "/path/to/models/dir:/app/models" model-converter`

This mounts the model directory into the docker image to convert each `.pkl` file into
their corresponding `.onnx` and `.json` sidecar files.
