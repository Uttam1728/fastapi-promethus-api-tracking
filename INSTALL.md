# Installation Guide

## Installing from GitHub using requirements.txt

To install the package directly from GitHub, add the following line to your requirements.txt file:

```
git+https://github.com/ushankradadiya/fastapi-prometheus-middleware.git@main
```

Then run:

```bash
pip install -r requirements.txt
```

## Installing from GitHub using pip

You can also install the package directly using pip:

```bash
pip install git+https://github.com/ushankradadiya/fastapi-prometheus-middleware.git@main
```

## Installing from PyPI

Once the package is published to PyPI, you can install it using pip:

```bash
pip install fastapi-prometheus-middleware
```

## Installing from Source

To install the package from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/ushankradadiya/fastapi-prometheus-middleware.git
   cd fastapi-prometheus-middleware
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

## Development Installation

For development, you can install the package with development dependencies:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastapi-prometheus-middleware.git
   cd fastapi-prometheus-middleware
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Building the Package

To build the package:

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade build
python -m build
```

This will create distribution packages in the `dist/` directory.

## Installing the Built Package

To install the built package:

```bash
python -m pip install dist/*.whl
```

Or you can use the provided script:

```bash
./build_and_install.sh
```
