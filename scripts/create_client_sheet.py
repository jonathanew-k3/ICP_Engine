import json
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

def create_client_config_sheet(client_name, template_id, creds_file="google-sheets-service-account.json"):
    # Set up credentials and Drive API
    scope = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    drive_service = build("drive", "v3", credentials=creds)

    # Define new sheet name
    new_title = f"{client_name} Config"

    PARENT_FOLDER_ID = "1WO-ub9-fnswe0QMicb2E3RMbeX8bloee"
    query = f"mimeType='application/vnd.google-apps.folder' and name='{client_name}' and '{PARENT_FOLDER_ID}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    folders = results.get("files", [])

    if folders:
        print(f"📁 Found existing folder for {client_name}")
        client_folder_id = folders[0]["id"]
    else:
        print(f"📁 Creating new folder for {client_name}")
        folder_metadata = {
            "name": client_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [PARENT_FOLDER_ID]
        }
        client_folder = drive_service.files().create(body=folder_metadata, fields="id", supportsAllDrives=True).execute()
        client_folder_id = client_folder.get("id")

    # Copy the template
    body = {
        "name": new_title,
        "parents": [client_folder_id]
    }
    new_file = drive_service.files().copy(fileId=template_id, body=body, fields="id", supportsAllDrives=True).execute()
    new_sheet_id = new_file.get("id")

    # Update sheet_map.json
    with open("sheet_map.json") as f:
        sheet_map = json.load(f)

    sheet_map[client_name] = new_sheet_id

    with open("sheet_map.json", "w") as f:
        json.dump(sheet_map, f, indent=2)

    print(f"✅ Created sheet for {client_name}: {new_sheet_id}")
    return new_sheet_id

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/create_client_sheet.py <ClientName> <TemplateSheetID>")
    else:
        client = sys.argv[1]
        template_id = sys.argv[2]
        create_client_config_sheet(client, template_id)
