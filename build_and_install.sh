#!/bin/bash

# Build the package
python -m pip install --upgrade pip
python -m pip install --upgrade build
python -m build

# Install the package
python -m pip install dist/*.whl --force-reinstall
