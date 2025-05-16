import gspread
import json
import sys
from pathlib import Path
from oauth2client.service_account import ServiceAccountCredentials
from scripts.generate_config_from_sheet import generate_config

def fetch_and_build(client_name, creds_file="google-sheets-service-account.json"):
    # Load sheet ID mapping
    with open("sheet_map.json") as f:
        sheet_map = json.load(f)

    if client_name not in sheet_map:
        raise ValueError(f"No sheet ID found for client: {client_name}")

    sheet_id = sheet_map[client_name]

    # Authenticate with Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    gclient = gspread.authorize(creds)

    # Open the sheet
    spreadsheet = gclient.open_by_key(sheet_id)

    # Generate the config.json file
    generate_config(
        client_name=client_name,
        schema_path="configs/shared/validation_schema.json"
    )

    print(f"✅ Config created for {client_name} at configs/{client_name}/config.json")

# Run from command line
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python fetch_and_build.py <client_name>")
        sys.exit(1)

    client_name = sys.argv[1]
    fetch_and_build(client_name)
