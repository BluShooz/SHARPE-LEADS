#!/usr/bin/env python3
"""
Sync Discovered Emails from Database to Google Sheets
"""

import sqlite3
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'
DB_PATH = 'leads.db'

def sync_emails_to_sheets():
    """Sync all leads with emails from database to Google Sheets"""

    print("=" * 60)
    print("🔄 Syncing Discovered Emails to Google Sheets")
    print("=" * 60)

    try:
        # Connect to Google Sheets
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(WORKSHEET_NAME)

        print("\n✅ Connected to Google Sheets")

        # Get all data from sheet
        all_data = worksheet.get_all_values()
        headers = all_data[0]
        data_rows = all_data[1:]

        # Find column indices
        company_col = 0  # Column A
        email_col = None

        if 'Confirmed Best Email' in headers:
            email_col = headers.index('Confirmed Best Email')

        if email_col is None:
            print("\n❌ 'Confirmed Best Email' column not found!")
            print(f"   Available columns: {headers[:10]}")
            return

        print(f"\n📊 Found {len(data_rows)} rows in Google Sheet")
        print(f"📧 Email column: Column {email_col + 1} (Confirmed Best Email)")

        # Create a mapping of company names to row numbers
        sheet_map = {}
        for i, row in enumerate(data_rows, start=2):
            company_name = row[company_col] if company_col < len(row) else ""
            if company_name:
                sheet_map[company_name.lower().strip()] = {
                    'row': i,
                    'current_email': row[email_col] if email_col < len(row) else ""
                }

        print(f"✅ Mapped {len(sheet_map)} companies from Google Sheet")

        # Get leads with emails from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT business_name, email, score, status
            FROM leads
            WHERE email IS NOT NULL
            AND email != ''
            ORDER BY score DESC
        ''')

        db_leads = cursor.fetchall()
        conn.close()

        print(f"\n📊 Found {len(db_leads)} leads with emails in database")

        if not db_leads:
            print("\n❌ No leads with emails found in database!")
            return

        # Match and update
        updates_to_make = []
        matched_count = 0

        for business_name, email, score, status in db_leads:
            company_key = business_name.lower().strip()

            if company_key in sheet_map:
                sheet_info = sheet_map[company_key]
                current_email = sheet_info['current_email']

                # Only update if email is different
                if current_email != email:
                    updates_to_make.append({
                        'row': sheet_info['row'],
                        'col': email_col + 1,  # Convert to 1-based for gspread
                        'company': business_name,
                        'email': email,
                        'current_email': current_email
                    })
                    matched_count += 1

        print(f"\n📝 Found {matched_count} matching leads")
        print(f"📝 Need to update {len(updates_to_make)} leads")

        if not updates_to_make:
            print("\n✅ All emails already in sync!")
            return

        # Show preview
        print("\n📋 Preview of Updates (first 5):")
        print("-" * 60)
        for i, update in enumerate(updates_to_make[:5], 1):
            print(f"{i}. {update['company'][:40]:40s}")
            print(f"   Row: {update['row']}")
            print(f"   Current: '{update['current_email']}'")
            print(f"   New: '{update['email']}'")
            print()

        if len(updates_to_make) > 5:
            print(f"... and {len(updates_to_make) - 5} more updates")

        # Confirm
        print("=" * 60)
        choice = input(f"\n❓ Update {len(updates_to_make)} leads in Google Sheet? (yes/no): ").strip().lower()

        if choice != 'yes':
            print("\n❌ Cancelled")
            return

        # Perform updates
        print("\n🔄 Updating Google Sheets...")
        print("-" * 60)

        updated_count = 0
        batch_size = 50
        batches = []

        for i in range(0, len(updates_to_make), batch_size):
            batch = updates_to_make[i:i+batch_size]
            batches.append(batch)

        for batch_num, batch in enumerate(batches, 1):
            # Prepare batch updates
            cells_to_update = []

            for update in batch:
                row = update['row']
                col = update['col']
                email = update['email']

                # Create cell notation
                col_letter = chr(64 + col) if col <= 26 else chr(64 + (col - 1) // 26) + chr(65 + (col - 1) % 26)
                cell_notation = f"{col_letter}{row}"

                cells_to_update.append({
                    'range': cell_notation,
                    'values': [[email]]
                })

                # Show progress
                print(f"   ✅ Row {row}: {update['company'][:40]:40s}")
                print(f"      {cell_notation} = {email}")

            # Update batch
            if cells_to_update:
                # Update one by one to avoid complex batch operations
                for cell_update in cells_to_update:
                    try:
                        worksheet.update(cell_update['range'], cell_update['values'])
                        updated_count += 1
                    except Exception as e:
                        print(f"      ⚠️  Failed to update {cell_update['range']}: {e}")

        print("\n" + "=" * 60)
        print(f"✅ SUCCESS! Updated {updated_count} leads in Google Sheet")
        print("=" * 60)

        print(f"\n📊 Summary:")
        print(f"   Processed: {len(db_leads)} leads from database")
        print(f"   Matched: {matched_count} leads in Google Sheet")
        print(f"   Updated: {updated_count} leads")
        print(f"   Skipped: {len(db_leads) - matched_count} leads (not in sheet)")

        print(f"\n💾 Sync completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n✅ Your Google Sheet now has all discovered emails!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        print("\n🔧 Possible issues:")
        print("   1. Service account doesn't have write permission")
        print("   2. Network connection issue")
        print("   3. Google Sheets API rate limit")

if __name__ == "__main__":
    sync_emails_to_sheets()
