# Intake OpenClimate

An intake catalog to read emissions data into Python. Data is loaded as a Pandas dataframe. This is a work in progress

```
├── LICENSE
├── README.md        <-- top-level documentation
├── catalogs/        <-- child catalogs
├── master.yaml      <-- main intake catalog
├── notebooks/       <-- example jupyter notebooks
└── scripts/         <-- python scripts to query database
```

## Requirements
If you are using Anaconda or Miniconda, install [`Intake`](https://intake.readthedocs.io/en/latest/index.html) with the following command:
```sh
conda install -c conda-forge intake
```

If you are using virtualenv/pip, do this:
```sh
pip install intake
```

## Usage
```python
import intake

# load catalog
catalog = "https://raw.githubusercontent.com/Open-Earth-Foundation/intake-OpenClimate/main/master.yaml"
cat = intake.open_catalog(catalog)

# list child catalogs
print(list(cat))

# list emissions datasets available
print(list(cat.emissions))

# load all actors from dataset
df = cat.emissions.unfccc.read()

# load single actor
df = cat.emissions.unfccc(actor='US").read()
```
