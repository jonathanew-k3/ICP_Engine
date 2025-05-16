import json
from pathlib import Path

def sync_priority_industries(source_client, target_client):
    base_path = Path("configs")

    source_file = base_path / source_client / "config.json"
    target_file = base_path / target_client / "config.json"

    # Load source and target configs
    with open(source_file) as f:
        source_config = json.load(f)

    with open(target_file) as f:
        target_config = json.load(f)

    # Copy priority industries
    target_config["priority_industries"] = source_config.get("priority_industries", [])

    # Save updated target config
    with open(target_file, "w") as f:
        json.dump(target_config, f, indent=2)

    print(f"✅ priority_industries synced from {source_client} → {target_client}")

if __name__ == "__main__":
    sync_priority_industries("konnect_insights", "KI_List")