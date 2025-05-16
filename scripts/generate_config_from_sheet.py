import json
from pathlib import Path
from jsonschema import validate
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def generate_config(client_name, schema_path):
    # Debug print using gspread to show the raw values in Blacklist Terms tab
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google-sheets-service-account.json", scope)
    client = gspread.authorize(creds)

    # Load sheet ID from sheet_map.json
    with open("sheet_map.json") as f:
        sheet_map = json.load(f)
    sheet_id = sheet_map.get(client_name)
    if not sheet_id:
        raise ValueError(f"No sheet ID found in sheet_map.json for client: {client_name}")

    sheet = client.open_by_key(sheet_id)
    try:
        values = sheet.worksheet("Blacklist Terms").get_all_values()
        print(f"📤 gspread fetched values from 'Blacklist Terms':\n{values}")
    except Exception as e:
        print(f"⚠️ Could not fetch 'Blacklist Terms' via gspread: {e}")

    config = {}

    # Sector Keywords
    rows = sheet.worksheet("Sector Keywords").get_all_records()
    sector_keywords = {}
    for row in rows:
        sector = row.get("Sector Name", "").strip()
        keyword = row.get("Keyword", "").strip()
        if sector and keyword:
            sector_keywords.setdefault(sector, []).append(keyword)
    config["sector_keywords"] = sector_keywords

    # Title Categories
    rows = sheet.worksheet("Title Categories").get_all_records()
    job_title_categories = {}
    for row in rows:
        category = row.get("Category", "").strip()
        title = row.get("Title Fragment", "").strip()
        if category and title:
            job_title_categories.setdefault(category, []).append(title)
    config["job_title_categories"] = job_title_categories

    # Blacklist Terms
    try:
        rows = sheet.worksheet("Blacklist Terms").get_all_records()
        config["blacklist_terms"] = [row["Term"].strip() for row in rows if row.get("Term")]
    except Exception as e:
        print(f"⚠️ Fallback: {e}")
        try:
            rows = sheet.worksheet("Blacklist Terms").get_all_records()
            config["blacklist_terms"] = [row["Term"].strip() for row in rows if row.get("Term")]
            print(f"✅ Loaded 'Blacklist Terms' via gspread fallback: {len(config['blacklist_terms'])} entries")
        except Exception as ge:
            raise ValueError(f"❌ Failed to load 'Blacklist Terms' via gspread: {ge}")

    # Priority Industries
    rows = sheet.worksheet("Priority Industries").get_all_records()
    config["priority_industries"] = [row["Industry Name"].strip() for row in rows if row.get("Industry Name")]

    # Role Seniority
    rows = sheet.worksheet("Role Seniority").get_all_records()
    role_seniority = {"senior": [], "mid": [], "junior": []}
    for row in rows:
        level = row.get("Level", "").strip().lower()
        term = row.get("Term", "").strip()
        if level in role_seniority and term:
            role_seniority[level].append(term)
    config["role_seniority"] = role_seniority

    # Excluded Companies
    rows = sheet.worksheet("Excluded Companies").get_all_records()
    config["excluded_companies"] = [row["Company Name"].strip() for row in rows if row.get("Company Name")]

    # Sector Negatives
    try:
        rows = sheet.worksheet("Sector Negatives").get_all_records()
        sector_negatives = {}
        for row in rows:
            sector = row.get("Sector", "").strip()
            term = row.get("Negative Term", "").strip()
            if sector and term:
                sector_negatives.setdefault(sector, []).append(term)
        config["sector_negatives"] = sector_negatives
    except Exception as e:
        raise ValueError(f"❌ Error reading 'Sector Negatives': {e}")

    # Add static config fields
    config.update({
        "client_name": client_name,
        "weights": {"reference_company": 10, "fuzzy_match": 5, "title_match": 5, "sector_match": 3},
        "fuzzy_threshold": 95.5,
        "confidence_bands": {"high": 12, "medium": 7},
        "exclusion_criteria": {"confidence_levels": ["Low"]},
        "geo_scoring": {
            "preferred": ["united kingdom", "germany"],
            "penalized": ["china", "india"]
        },
        "reference_companies_file": "Reference_Companies.csv"
    })

    # Validate against schema
    with open(schema_path) as f:
        schema = json.load(f)
    validate(instance=config, schema=schema)

    # Save to configs/{client}/config.json
    output_path = Path(f"configs/{client_name}/config.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ config.json written to {output_path}")
