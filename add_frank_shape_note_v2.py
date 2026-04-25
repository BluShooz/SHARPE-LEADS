#!/usr/bin/env python3
"""
Add note for Frank Shape - Find an unprotected column
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
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("\n✅ Connected to Google Sheet")

    # Get headers
    headers = worksheet.row_values(1)

    # Try different columns to find an unprotected one
    columns_to_try = [
        'Next Best Action',
        'Last Outcome Note',
        'Caller Summary',
        'Closer Handoff Summary',
        'FNA Recommended Offer'
    ]

    working_col = None
    working_col_index = None

    for col_name in columns_to_try:
        if col_name in headers:
            col_index = headers.index(col_name)
            col_letter = chr(64 + (col_index + 1)) if col_index + 1 <= 26 else chr(64 + ((col_index + 1) - 1) // 26) + chr(65 + ((col_index + 1) - 1) % 26)

            print(f"\n🧪 Testing column: {col_name} (Column {col_letter})...")

            try:
                # Try to read and write to row 2
                test_cell = f"{col_letter}2"
                current_value = worksheet.acell(test_cell).value

                # Try to write
                worksheet.update([[""]], test_cell)
                # Revert
                worksheet.update([[current_value]], test_cell)

                working_col = col_name
                working_col_index = col_index
                working_col_letter = col_letter

                print(f"   ✅ Column '{col_name}' is UNPROTECTED!")
                break

            except Exception as e:
                print(f"   🔒 Column '{col_name}' is protected")

    if working_col is None:
        print("\n❌ No unprotected columns found!")
        print("\n💡 Alternative: Manually add note to Google Sheet")
        print("   1. Open your Google Sheet")
        print("   2. Find 5 leads without emails")
        print("   3. Add to Notes column: 'Frank Shape: check out these leads'")
        exit(0)

    print(f"\n✅ Using column: {working_col} (Column {working_col_letter})")

    # Find 5 leads to add the note to
    all_data = worksheet.get_all_values()
    data_rows = all_data[1:]
    company_col = 0

    leads_to_update = []

    for i, row in enumerate(data_rows[:10], start=2):
        company = row[company_col] if company_col < len(row) else ""

        if company:
            leads_to_update.append({
                'row': i,
                'company': company
            })

        if len(leads_to_update) >= 5:
            break

    print(f"\n📋 Adding note to {min(5, len(leads_to_update))} leads...")

    frank_note = "Frank Shape: check out these leads"
    notes_added = 0

    for lead in leads_to_update[:5]:
        row = lead['row']
        cell_notation = f"{working_col_letter}{row}"

        try:
            # Get current value
            current_value = worksheet.acell(cell_notation).value

            # Add Frank Shape note
            new_value = f"{current_value} | Frank Shape: check out these leads" if current_value else frank_note

            worksheet.update([[new_value]], cell_notation)

            print(f"   ✅ Row {row}: {lead['company'][:40]:40s}")
            print(f"      Added: '{frank_note}'")
            notes_added += 1

        except Exception as e:
            print(f"   ❌ Row {row}: Failed - {e}")

    print("\n" + "=" * 60)
    print(f"✅ SUCCESS! Added note to {notes_added} leads")
    print("=" * 60)

    print(f"\n📝 Note added: 'Frank Shape: check out these leads'")
    print(f"📊 Added to: Column {working_col_letter} ({working_col})")

    print(f"\n💡 To find these leads:")
    print(f"   1. Open your Google Sheet")
    print(f"   2. Use Ctrl+F and search for 'Frank Shape'")
    print(f"   3. Filter by the {working_col} column")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
