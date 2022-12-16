# Intake OpenClimate

An intake catalog to read emissions data into Python. Data is loaded as a Pandas dataframe. This is a work in progress

## Requirements
This requires having [`intake`](https://intake.readthedocs.io/en/latest/index.html) intalled:

If you are using Anaconda or Miniconda, install Intake with the following commands:
```sh
conda install -c conda-forge intake
```

If you are using virtualenv/pip, run the following command:
```sh
pip install intake
```

## Usage
Open the data catalog:
```python
import intake

catalog = "https://raw.githubusercontent.com/Open-Earth-Foundation/intake-OpenClimate/main/master.yaml"
cat = intake.open_catalog(catalog)
```

List the available emissions datasets:
```python
print(list(cat.emissions))
```

Load an entire dataset:
```python
df = cat.emissions.unfccc.read()
```

Load a specific actor:
```python
actor='US'
df = cat.emissions.unfccc(actor=actor).read()
```