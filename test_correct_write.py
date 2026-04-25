#!/usr/bin/env python3
"""
Test Google Sheets Write - Correct API Usage
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

print("=" * 60)
print("🧪 Testing Google Sheets Write (Correct API)")
print("=" * 60)

try:
    # Connect
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("\n✅ Connected to Google Sheets")

    # Get headers to find email column
    headers = worksheet.row_values(1)
    print(f"\n📋 Total columns: {len(headers)}")

    # Find "Confirmed Best Email" column
    if 'Confirmed Best Email' in headers:
        email_col_index = headers.index('Confirmed Best Email')
        print(f"✅ Found 'Confirmed Best Email' at column {email_col_index + 1}")

        # Convert to column letter (AL = column 38)
        col_letter = chr(64 + (email_col_index + 1)) if email_col_index + 1 <= 26 else chr(64 + ((email_col_index + 1) - 1) // 26) + chr(65 + ((email_col_index + 1) - 1) % 26)
        print(f"📧 Column letter: {col_letter}")

        # Test writing to row 3 (not row 2 which might have formatting issues)
        test_row = 3
        test_cell = f"{col_letter}{test_row}"
        test_email = "test@example.com"

        print(f"\n🧪 Testing write to {test_cell}...")

        # Read current value first
        current_value = worksheet.acell(test_cell).value
        print(f"   Current value: '{current_value}'")

        # Write test email using correct API (values first, range second)
        try:
            worksheet.update(
                [[test_email]],  # values
                test_cell       # range_name
            )
            print(f"   ✅ WRITE SUCCESSFUL!")

            # Verify it was written
            new_value = worksheet.acell(test_cell).value
            print(f"   New value: '{new_value}'")

            # Clean up - revert to original value
            worksheet.update(
                [[current_value]],
                test_cell
            )
            print(f"   ✅ Cleaned up test data")

            print("\n" + "=" * 60)
            print("🎉 SUCCESS! Write permissions are working!")
            print("=" * 60)
            print("\n✅ Your service account CAN write to the email column!")
            print("✅ Ready to sync discovered emails to Google Sheet!")

            print("\n📝 Next step: Run the sync script")
            print("   python3 sync_emails_to_sheets.py")

        except Exception as write_error:
            print(f"   ❌ Write failed: {write_error}")
            print(f"\n🔧 Possible issues:")
            print(f"   1. Cell has special formatting/validation")
            print(f"   2. Row is protected")
            print(f"   3. Column has dropdown menus")

            print(f"\n💡 Try a different row...")

            # Try row 10 instead
            test_row = 10
            test_cell = f"{col_letter}{test_row}"

            try:
                current_value = worksheet.acell(test_cell).value
                worksheet.update([[test_email]], test_cell)
                print(f"   ✅ Row {test_row} works!")

                # Clean up
                worksheet.update([[current_value]], test_cell)

                print(f"\n✅ SUCCESS using row {test_row}!")
                print(f"💡 We'll update from row 2, but skip protected rows")

            except Exception as e2:
                print(f"   ❌ Row {test_row} also failed: {e2}")

    else:
        print(f"\n❌ 'Confirmed Best Email' column not found!")
        print(f"\n📋 Available columns:")
        for i, h in enumerate(headers[:20], 1):
            print(f"   {i:2d}. {h}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
