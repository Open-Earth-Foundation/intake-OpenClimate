import intake

def open_catalog():
    catalog = 'https://raw.githubusercontent.com/Open-Earth-Foundation/intake-OpenClimate/main/master.yaml'
    return intake.open_catalog(catalog)
