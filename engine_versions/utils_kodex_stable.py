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

def normalize_company(name):
    return name.strip().lower()

def match_company(name, company_map):
    return company_map.get(name, name)

def load_reference_companies(path):
    df = pd.read_csv(path)
    df['normalized_company'] = df['Company'].str.lower().str.strip()
    return df
