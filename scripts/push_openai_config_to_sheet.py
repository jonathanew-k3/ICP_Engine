import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

def push_to_sheet(client_name, json_path="openai_config_suggestions.json", creds_file="google-sheets-service-account.json"):
    # Load AI-generated config suggestions
    with open(json_path) as f:
        config = json.load(f)

    # Load sheet ID mapping
    with open("sheet_map.json") as f:
        sheet_map = json.load(f)

    if client_name not in sheet_map:
        raise ValueError(f"No sheet ID found for client: {client_name}")

    sheet_id = sheet_map[client_name]

    # Authorize and connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)

    def write_tab(tab_name, rows):
        try:
            worksheet = spreadsheet.worksheet(tab_name)
            worksheet.clear()
            if rows:
                worksheet.update([list(rows[0].keys())] + [list(r.values()) for r in rows])
            print(f"✅ Updated tab: {tab_name}")
        except Exception as e:
            print(f"⚠️ Failed to update {tab_name}: {e}")

    # Priority Industries
    write_tab("Priority Industries", [{"Industry Name": i} for i in config.get("priority_industries", [])])

    # Sector Keywords
    sk_data = []
    for sector, keywords in config.get("sector_keywords", {}).items():
        for keyword in keywords:
            sk_data.append({"Sector Name": sector, "Keyword": keyword})
    write_tab("Sector Keywords", sk_data)

    # Blacklist Terms
    bl_data = [{"Term": term} for term in config.get("blacklist_terms", [])]
    write_tab("Blacklist Terms", bl_data)

    # Title Categories
    tc_data = []
    for category, fragments in config.get("job_title_categories", {}).items():
        for title in fragments:
            tc_data.append({"Category": category, "Title Fragment": title})
    write_tab("Title Categories", tc_data)

    # Role Seniority
    rs_data = []
    for level, terms in config.get("role_seniority", {}).items():
        for term in terms:
            rs_data.append({"Level": level, "Term": term})
    write_tab("Role Seniority", rs_data)

    print("🎯 Done pushing AI config to sheet.")

# CLI support
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/push_openai_config_to_sheet.py <ClientName>")
    else:
        push_to_sheet(sys.argv[1])