import json
from pathlib import Path

def create_client_config(client_name):
    base_path = Path("configs") / client_name

    # Load settings.json
    with open(base_path / "settings.json") as f:
        settings = json.load(f)

    # Load priority_industries.json if it exists
    priority_path = base_path / "priority_industries.json"
    if priority_path.exists():
        with open(priority_path) as f:
            priority_industries = json.load(f)
    else:
        priority_industries = []

    # Add new fields
    settings["priority_industries"] = priority_industries
    settings["reference_companies_file"] = "Reference_Companies.csv"

    # Save merged config
    config_path = base_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"✅ Created: {config_path}")

clients = ["konnect_insights", "KI_List", "kodex"]

for client in clients:
    create_client_config(client)