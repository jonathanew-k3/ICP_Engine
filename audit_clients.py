import os

CONFIG_ROOT = "configs"
DATA_ROOT = "data"
EXCLUDED_CLIENTS = {"shared"}
EXPECTED_CONFIG_FILES = {"settings.json", "Reference_Companies.csv", "priority_industries.json"}
EXPECTED_DATA_FILES = {"Source_Data.csv"}

def list_files(folder):
    return set(os.listdir(folder)) if os.path.exists(folder) else set()

def audit_client(client):
    if client in EXCLUDED_CLIENTS:
        return

    print(f"\n🔍 Auditing client: {client}")

    config_path = os.path.join(CONFIG_ROOT, client)
    data_path = os.path.join(DATA_ROOT, client)

    config_files = list_files(config_path)
    data_files = list_files(data_path)

    # Check for missing config files
    missing_config = EXPECTED_CONFIG_FILES - config_files
    if missing_config:
        print(f"  ⚠️ Missing in configs/{client}: {', '.join(missing_config)}")

    # Extra config files
    extra_config = config_files - EXPECTED_CONFIG_FILES
    if extra_config:
        print(f"  🧹 Extra files in configs/{client}: {', '.join(extra_config)}")

    # Check for missing data files
    missing_data = EXPECTED_DATA_FILES - data_files
    if missing_data:
        print(f"  ⚠️ Missing in data/{client}: {', '.join(missing_data)}")

    # Extra data files
    extra_data = data_files - EXPECTED_DATA_FILES
    if extra_data:
        print(f"  🧹 Extra files in data/{client}: {', '.join(extra_data)}")

def main():
    clients = sorted(os.listdir(CONFIG_ROOT))
    for client in clients:
        if os.path.isdir(os.path.join(CONFIG_ROOT, client)) and client not in EXCLUDED_CLIENTS:
            audit_client(client)

if __name__ == "__main__":
    main()
