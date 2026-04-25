#!/usr/bin/env python3
"""
Test Google Sheets Write Permissions
"""

import gspread
from google.oauth2.service_account import Credentials
import sys

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

print("=" * 60)
print("🧪 Testing Google Sheets Write Permissions")
print("=" * 60)

try:
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("\n✅ Connected to Google Sheets")

    # Test 1: Read a cell
    test_cell = "A2"
    original_value = worksheet.acell(test_cell).value
    print(f"✅ Test 1: READ cell {test_cell} = '{original_value}'")

    # Test 2: Write to a cell (same value to test permissions)
    worksheet.update(test_cell, [[original_value]])
    print(f"✅ Test 2: WRITE cell {test_cell} - SUCCESS!")

    # Test 3: Try to find and update an email cell
    print(f"\n🧪 Test 3: Update Email Cell")
    print("-" * 60)

    # Get column letter for "Confirmed Best Email"
    headers = worksheet.row_values(1)

    if 'Confirmed Best Email' in headers:
        email_col_index = headers.index('Confirmed Best Email') + 1
        email_col_letter = chr(64 + email_col_index) if email_col_index <= 26 else chr(64 + (email_col_index - 1) // 26) + chr(65 + (email_col_index - 1) % 26)

        print(f"📧 Email column: {email_col_letter} ({email_col_index})")

        # Find first row with empty email
        all_data = worksheet.get_all_values()

        for i, row in enumerate(all_data[1:11], 2):  # Check first 10 data rows
            row_index = i

            # Get email value
            email_value = row[email_col_index - 1] if email_col_index - 1 < len(row) else ""

            company_name = row[0] if len(row) > 0 else ""

            if not email_value.strip() and company_name:
                # Try to update this row with a test email
                test_email = f"test.{row_index}@example.com"

                # Use update with cell notation
                cell_notation = f"{email_col_letter}{row_index}"
                worksheet.update(cell_notation, [[test_email]])

                print(f"   ✅ Updated row {row_index} ({company_name[:30]:30s})")
                print(f"      Cell: {cell_notation} = {test_email}")

                # Test passed
                print("\n" + "=" * 60)
                print("✅ WRITE PERMISSIONS WORKING!")
                print("=" * 60)
                print("\n🎉 Your service account can now write to Google Sheets!")
                print("\n📝 Next steps:")
                print("   1. Run: python3 sync_emails_to_sheets.py")
                print("   2. This will sync all discovered emails to your sheet")

                # Clean up - revert the test update
                print(f"\n🧹 Cleaning up test data...")
                worksheet.update(cell_notation, [[""]])

                sys.exit(0)

        print("\n⚠️  All email cells in first 10 rows are filled")
    else:
        print(f"\n❌ Column 'Confirmed Best Email' not found!")
        print(f"   Available columns: {headers[:10]}")

except Exception as e:
    print(f"\n❌ Test FAILED: {e}")
    print("\n🔧 Permission error detected!")
    print("\n📋 Fix:")
    print("   1. Open your Google Sheet")
    print("   2. Click 'Share' button")
    print("   3. Add service account email as 'Editor'")
    print("   4. Wait 30-60 seconds")
    print("   5. Run this test again")

print("\n" + "=" * 60)
