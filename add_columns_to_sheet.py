#!/usr/bin/env python3
"""
LeadForge AI - Add Professional Columns to Google Sheet
Automatically adds missing columns for professional lead management
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List

# Configuration
SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Columns to add (in order)
NEW_COLUMNS = [
    'Contact Name',
    'Email',
    'Business Hours',
    'Last Contact Date',
    'Next Action',
    'Source',
    'Facebook',
    'Instagram',
    'LinkedIn',
    'Owner Name',
    'Estimated Value',
    'Tags',
    'Notes'
]


def add_columns_to_sheet():
    """
    Add missing professional columns to Google Sheet
    """
    try:
        print("=" * 60)
        print("🚀 Adding Professional Columns to Google Sheet")
        print("=" * 60)

        # Define the scope
        scope = ['https://www.googleapis.com/auth/spreadsheets']

        # Load service account credentials
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(WORKSHEET_NAME)

        print(f"✅ Connected to sheet: {WORKSHEET_NAME}")

        # Get all existing columns
        all_data = worksheet.get_all_records()
        if not all_data:
            print("❌ Sheet is empty or has no data")
            return False

        existing_columns = list(all_data[0].keys())
        print(f"📋 Existing columns: {existing_columns}")

        # Find which columns are missing
        missing_columns = []
        for col in NEW_COLUMNS:
            if col not in existing_columns:
                missing_columns.append(col)

        if not missing_columns:
            print("\n✅ All professional columns already exist!")
            print(f"   Current columns: {existing_columns}")
            return True

        print(f"\n📝 Missing columns to add: {missing_columns}")

        # Add missing columns
        # Find the last column index (after "Call Status")
        try:
            # Find the index of "Call Status" column
            if "Call Status" in existing_columns:
                insert_after = existing_columns.index("Call Status") + 1
            else:
                insert_after = len(existing_columns)

            # Add columns one by one
            for i, col_name in enumerate(missing_columns):
                # Convert column letter to number (A=1, B=2, etc.)
                col_letter = gspread.utils.rowcol_to_alpha(1, insert_after + i)

                # Add column header
                worksheet.update_value(f"{col_letter}1", col_name)
                print(f"   ✅ Added column: {col_name} (position {insert_after + i})")

            print(f"\n✅ Successfully added {len(missing_columns)} new columns!")

            # Verify the changes
            all_data = worksheet.get_all_records()
            new_columns = list(all_data[0].keys())
            print(f"\n📊 New total columns: {len(new_columns)}")
            print(f"   Columns: {new_columns}")

        except Exception as e:
            print(f"\n❌ Error adding columns: {e}")
            print("\n💡 Alternative: Manually add these columns in Google Sheets:")
            for col in missing_columns:
                print(f"   - {col}")
            return False

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📋 Setup Instructions:")
        print("1. Create service account in Google Cloud Console")
        print("2. Download service account JSON key as 'service_account.json'")
        print("3. Share your Google Sheet with the service account email")
        return False


def main():
    """Main execution"""
    print("\n🎯 LeadForge AI - Google Sheet Column Updater")
    print("=" * 60)
    print("\nThis script will add professional lead management columns to your Google Sheet.")
    print("\nColumns to be added:")
    for i, col in enumerate(NEW_COLUMNS, 1):
        print(f"  {i}. {col}")
    print("\n" + "=" * 60)

    success = add_columns_to_sheet()

    if success:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Your Google Sheet now has professional columns!")
        print("=" * 60)
        print("\n✅ Next steps:")
        print("1. Open your Google Sheet")
        print("2. You'll see the new columns added")
        print("3. Start filling in the data (contact names, emails, etc.)")
        print("4. Export CSV to see all 23 fields!")
        print("\n🔗 Google Sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    else:
        print("\n" + "=" * 60)
        print("❌ Could not add columns automatically")
        print("=" * 60)
        print("\n💡 Manual instructions:")
        print("1. Open your Google Sheet")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
        print("2. Right-click on the 'Call Status' column")
        print("3. Select 'Insert 1 column to the right'")
        print("4. Add these columns:")
        for col in NEW_COLUMNS:
            print(f"   - {col}")
        print("5. Save the sheet")


if __name__ == "__main__":
    main()
