from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastapi-prometheus-middleware",
    version="0.1.0",
    author="Ushank Radadiya",
    author_email="ushankradadiya@gofynd.com",
    description="A middleware for FastAPI applications that tracks and exposes Prometheus metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ushankradadiya/fastapi-prometheus-middleware",
    project_urls={
        "Bug Tracker": "https://github.com/ushankradadiya/fastapi-prometheus-middleware/issues",
        "Documentation": "https://github.com/ushankradadiya/fastapi-prometheus-middleware#readme",
        "Source Code": "https://github.com/ushankradadiya/fastapi-prometheus-middleware",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.7",
    install_requires=[
        "fastapi>=0.68.0",
        "prometheus-client>=0.12.0",
        "starlette>=0.14.2",
        "orjson>=3.6.0",
    ],
)
