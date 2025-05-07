import json
import pandas as pd
import os

def load_config(config_name):
    base_path = os.path.join("configs", config_name)
    with open(os.path.join(base_path, "company_map.json")) as f:
        company_map = json.load(f)["company_group_map"]
    with open(os.path.join(base_path, "settings.json")) as f:
        settings = json.load(f)
    return company_map, settings

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

def match_company(name, company_map):
    return company_map.get(name, name)

def load_reference_companies(path):
    df = pd.read_csv(path)
    df['normalized_company'] = df['Company'].str.lower().str.strip()
    return df
