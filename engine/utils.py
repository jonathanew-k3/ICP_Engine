import json
import pandas as pd
import os

def load_config(config_name):
    import jsonschema  # ensure this is installed in your environment
    from jsonschema import validate

    base_path = os.path.join("configs", config_name)
    config_path = os.path.join(base_path, "config.json")
    schema_path = os.path.join("configs", "shared", "validation_schema.json")

    # Load config
    with open(config_path) as f:
        config = json.load(f)

    # Load and validate against schema
    with open(schema_path) as f:
        schema = json.load(f)

    validate(instance=config, schema=schema)

    return config

import re

def normalize_company(name):
    if not isinstance(name, str):
        return ""
    name = name.strip().lower()

    # Remove common suffixes
    suffixes = [
        r'\binc\b', r'\bltd\b', r'\bllc\b', r'\bgmbh\b', r'\bplc\b', r'\bcorp\b',
        r'\bco\b', r'\bsa\b', r'\bspa\b', r'\bsarl\b', r'\bkk\b', r'\bab\b', r'\bas\b',
        r'\bpvt\b', r'\bprivate\b', r'\blimited\b', r'\bcompany\b', r'\bag\b', r'\bincorporated\b',
        r'\bgroup\b', r'\bhldgs\b', r'\bhldg\b', r'\bholdings\b'
    ]
    pattern = r'\s*(?:' + '|'.join(suffixes) + r')[\.,]?\b'
    name = re.sub(pattern, '', name)

    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_company_group_name(company_name, company_map):
    if not isinstance(company_name, str):
        return ""
    return company_map.get(company_name.strip().lower(), company_name.strip().lower())
    
def load_reference_companies(path):
    df = pd.read_csv(path)
    df['normalized_company'] = df['Company'].str.lower().str.strip()
    return df
