# Intake OpenClimate

An intake catalog to read emissions data into Python. Data is loaded as a Pandas dataframe. This is a work in progress

```
├── LICENSE
├── README.md        <-- top-level documentation
├── catalogs/        <-- child catalogs
├── master.yaml      <-- main intake catalog
├── notebooks/       <-- example jupyter notebooks
├── scripts/         <-- python scripts to query database
└── src/             <-- python package source code
```

## Installation
```sh
pip install -e git+https://github.com/Open-Earth-Foundation/intake-OpenClimate.git#egg=intake-OpenClimate
```
For now you can only install the package via GitHub, soon it will be available on `PyPi` and `conda`

## Usage
```python
import intake_openclimate as oc

# load catalog
cat = oc.open_catalog()

# list child catalogs
print(list(cat))

# list emissions datasets available
print(list(cat.emissions))

# load all actors from dataset
df = cat.emissions.unfccc.read()

# load single actor
df = cat.emissions.unfccc(actor="US").read()
```
