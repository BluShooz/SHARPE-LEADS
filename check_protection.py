#!/usr/bin/env python3
"""
Workaround: Check which cells/rows are protected and find unprotected areas
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

print("=" * 60)
print("🔍 Google Sheet Protection Check")
print("=" * 60)

try:
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("\n✅ Connected to Google Sheets")

    # Get all data to understand the structure
    all_data = worksheet.get_all_values()
    headers = all_data[0]

    print(f"\n📊 Total rows: {len(all_data)}")
    print(f"📋 Total columns: {len(headers)}")

    # Find the email column
    if 'Confirmed Best Email' in headers:
        email_col_idx = headers.index('Confirmed Best Email')
        print(f"\n📧 Email column found: Column {email_col_idx + 1} (Confirmed Best Email)")

        # Try to write to different rows to find unprotected ones
        print("\n🧪 Testing write access to different rows...")
        print("-" * 60)

        unprotected_rows = []

        # Test rows 2-20
        for row_num in range(2, min(22, len(all_data))):
            cell_notation = f"AL{row_num}"  # AL is the email column

            try:
                # Try to read first
                current_value = worksheet.acell(cell_notation).value

                # Try to write the same value back (test)
                worksheet.update(cell_notation, [[current_value]], value_input_option='RAW')

                unprotected_rows.append(row_num)
                print(f"   ✅ Row {row_num}: UNPROTECTED (can write)")

            except Exception as e:
                error_msg = str(e)
                if 'protected' in error_msg.lower():
                    print(f"   🔒 Row {row_num}: PROTECTED")
                else:
                    print(f"   ❌ Row {row_num}: ERROR - {error_msg}")

        print("\n" + "=" * 60)

        if unprotected_rows:
            print(f"\n✅ Found {len(unprotected_rows)} unprotected rows")
            print(f"   Rows: {unprotected_rows[:10]}")

            if len(unprotected_rows) >= 1:
                print(f"\n💡 SOLUTION: Update only unprotected rows")
                print(f"   Can update {len(unprotected_rows)} leads with emails")
        else:
            print("\n❌ All tested rows are protected!")
            print("\n🔧 SOLUTION: Remove sheet protection")
            print("   1. Open Google Sheet")
            print("   2. Data → Protect sheets and ranges")
            print("   3. Remove all protections")
            print("   4. Or: File → Protect sheet → Unprotect sheet")

    else:
        print(f"\n❌ 'Confirmed Best Email' column not found!")
        print(f"   Available columns: {[h[:30] for h in headers[:10]]}")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
