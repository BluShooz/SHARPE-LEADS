#!/usr/bin/env python3
"""
Add note for Frank Shape to processed leads in Google Sheet
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

print("=" * 60)
print("📝 Adding Frank Shape Note to Google Sheet")
print("=" * 60)

try:
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("\n✅ Connected to Google Sheets")

    # Get all data
    all_data = worksheet.get_all_values()
    headers = all_data[0]

    # Find relevant columns
    company_col = 0
    notes_col = None

    if 'Notes' in headers:
        notes_col = headers.index('Notes')
    else:
        print(f"\n❌ 'Notes' column not found!")
        print(f"   Available columns: {[h[:30] for h in headers[:10]]}")
        exit(1)

    print(f"\n📝 Notes column found: Column {notes_col + 1}")

    # Find leads that were just processed (first 10 with empty emails)
    data_rows = all_data[1:]
    processed_rows = []

    for i, row in enumerate(data_rows[:20], start=2):
        if len(row) > notes_col:
            notes = row[notes_col] if notes_col < len(row) else ""
            company = row[company_col] if company_col < len(row) else ""

            if company and not notes.strip():
                processed_rows.append({
                    'row': i,
                    'company': company,
                    'current_notes': notes
                })

            if len(processed_rows) >= 10:
                break

    print(f"\n📋 Found {len(processed_rows)} leads to add note")

    if not processed_rows:
        print("\n❌ No leads found to add note")
        exit(1)

    # Add Frank Shape note
    notes_to_add = 5
    notes_added = 0

    for lead in processed_rows[:notes_to_add]:
        row = lead['row']
        company = lead['company']
        cell_notation = f"AR{row}"  # Notes column

        # Create note
        frank_note = "Frank Shape: check out these leads"

        try:
            worksheet.update(
                [[frank_note]],
                cell_notation
            )
            print(f"   ✅ Row {row}: {company[:40]:40s}")
            print(f"      Added: '{frank_note}'")
            notes_added += 1

        except Exception as e:
            print(f"   ❌ Row {row}: Failed - {e}")

    print("\n" + "=" * 60)
    print(f"✅ SUCCESS! Added note to {notes_added} leads")
    print("=" * 60)

    print(f"\n📝 Note added: 'Frank Shape: check out these leads'")
    print(f"📊 Added to: Column AR (Notes)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n💡 Next steps:")
print("   1. Open your Google Sheet")
print("   2. Filter by 'Frank Shape' in the Notes column")
print("   3. Review the leads with the note")
