"""
LeadForge AI - Google Sheets Integration Module
Reads from and writes to Google Sheets using Service Account
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Google Sheets Configuration
SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "Imported Leads Clean"  # Updated: Use clean worksheet with NO duplicates
SERVICE_ACCOUNT_FILE = '/Users/jonsmith/leadforge-scraper/service_account.json'  # Full path

# Column mappings (Google Sheet column -> LeadForge field)
COLUMN_MAPPING = {
    'Primary Link': 'website',
    'Source Link': 'source_url',
    'Phone': 'phone',
    'Market': 'location',
    'Presence Type': 'presence_type',
    'Caller Owner': 'caller_owner',
    'Opportunity Stage': 'opportunity_stage',
    'Call Status': 'call_status',
    'Next Follow Up': 'next_follow_up',
    'Next Best Action': 'next_best_action',
    'Weighted Opportunity Value': 'opportunity_value',
    'Difficulty': 'difficulty'
}


class GoogleSheetsClient:
    def __init__(self):
        """
        Initialize Google Sheets client using Service Account

        Setup instructions:
        1. Create service account in Google Cloud Console
        2. Download service account JSON key as 'service_account.json'
        3. Share your Google Sheet with the service account email
        """
        try:
            # Define the scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']

            # Load service account credentials
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)

            # Authorize the client
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(SHEET_ID)
            self.worksheet = self.sheet.worksheet(WORKSHEET_NAME)
            print("✅ Connected to Google Sheets successfully!")
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {e}")
            print("\n📋 Setup Instructions:")
            print("1. Create service account in Google Cloud Console")
            print("2. Download service account JSON key as 'service_account.json'")
            print("3. Share your Google Sheet with the service account email")
            self.worksheet = None

    def read_all_leads(self):
        """Read all leads from Google Sheets"""
        if not self.worksheet:
            return []

        try:
            # Get all data
            data = self.worksheet.get_all_records()

            leads = []
            for row in data:
                # Get actual company name from Business Name column
                company = row.get('Business Name', '')
                if not company:
                    continue  # Skip rows without company names

                lead = {
                    # Essential fields - Match "Imported Leads" worksheet columns
                    'business_name': company,
                    'phone': row.get('Phone', ''),
                    'email': row.get('Email', ''),
                    'website': row.get('Website', ''),
                    'location': row.get('Location', ''),
                    'industry': row.get('Industry', 'Business'),
                    'source': 'Google Sheets',
                    'status': 'new',
                    'stage': 'PROSPECT',
                    'score': int(row.get('Score', 70)) if row.get('Score') else 70,
                    'rating': float(row.get('Rating', 0)) if row.get('Rating') else None,
                    'reviews_count': int(row.get('Reviews', 0)) if row.get('Reviews') else 0,
                    'address': row.get('Address', ''),

                    # Additional fields
                    'contact_name': '',
                    'business_hours': '',
                    'last_contact_date': '',
                    'next_action': 'PLACE FIRST CALL',
                    'owner_name': '',
                    'estimated_value': '',
                    'facebook': '',
                    'instagram': '',
                    'linkedin': '',
                    'tags': '',
                    'notes': '',
                    'created_at': '',
                    'last_updated': datetime.now().isoformat()
                }
                leads.append(lead)

            print(f"✅ Read {len(leads)} leads from Google Sheets")
            return leads

        except Exception as e:
            print(f"❌ Error reading leads: {e}")
            return []

    def add_lead_to_sheet(self, lead):
        """Add a single lead to Google Sheets with duplicate prevention"""
        if not self.worksheet:
            return False

        try:
            # Check for duplicate before adding
            business_name = lead.get('business_name', '').lower().strip()

            # Get all existing business names
            all_data = self.worksheet.get_all_values()
            existing_names = set()
            for row in all_data[1:]:  # Skip header
                if row and len(row) > 0:
                    existing_names.add(row[0].lower().strip())

            # Skip if duplicate
            if business_name in existing_names:
                print(f"⚠️  Skipped duplicate lead: {lead.get('business_name')}")
                return False

            # Map lead to sheet columns
            row = [
                lead.get('business_name', ''),
                lead.get('phone', ''),
                lead.get('website', ''),
                lead.get('location', ''),
                lead.get('industry', ''),
                str(lead.get('rating', '')) if lead.get('rating') else '',
                str(lead.get('reviews_count', '')) if lead.get('reviews_count') else '',
                lead.get('address', ''),
                lead.get('email', ''),
                str(lead.get('score', 70))
            ]

            self.worksheet.append_row(row)
            print(f"✅ Added lead to Google Sheets: {lead.get('business_name')}")
            return True

        except Exception as e:
            print(f"❌ Error adding lead to sheet: {e}")
            return False

    def add_leads_to_sheet(self, leads):
        """Add multiple leads to Google Sheets in batch"""
        if not self.worksheet:
            return 0

        added_count = 0
        for lead in leads:
            if self.add_lead_to_sheet(lead):
                added_count += 1

        return added_count

    def update_lead_status(self, row_number, status):
        """Update lead status in Google Sheets"""
        if not self.worksheet:
            return False

        try:
            # Find Call Status column (column H)
            self.worksheet.update_cell(row_number, 8, status.upper())
            print(f"✅ Updated row {row_number} status to {status}")
            return True
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False


def import_leads_to_database(sheets_client, db_path):
    """Import leads from Google Sheets to SQLite database"""
    from main import save_lead_to_db

    leads = sheets_client.read_all_leads()

    if not leads:
        print("❌ No leads to import")
        return 0

    imported_count = 0
    for lead in leads:
        try:
            lead_id = save_lead_to_db(lead)
            imported_count += 1
            print(f"✅ Imported: {lead['business_name']} (ID: {lead_id})")
        except Exception as e:
            print(f"❌ Error importing lead: {e}")

    print(f"\n🎉 Successfully imported {imported_count}/{len(leads)} leads to database!")
    return imported_count


def export_new_leads_to_sheets(sheets_client, db_path):
    """Export new leads from database to Google Sheets"""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get leads not yet exported
    cursor.execute('''
        SELECT * FROM leads WHERE status = 'new'
        ORDER BY created_at DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    leads = []
    for row in rows:
        lead = {
            'id': row[0],
            'business_name': row[1],
            'industry': row[2],
            'location': row[3],
            'phone': row[4],
            'website': row[5],
            'rating': row[6],
            'reviews_count': row[7],
            'address': row[8],
            'email': row[9],
            'score': row[10],
            'status': row[11],
            'created_at': row[12]
        }
        leads.append(lead)

    exported_count = sheets_client.add_leads_to_sheet(leads)

    print(f"\n🎉 Exported {exported_count}/{len(leads)} new leads to Google Sheets!")
    return exported_count


# Standalone functions for quick usage
def quick_import():
    """Quick import: Pull all leads from Google Sheets to database"""
    print("🚀 Starting Google Sheets import...")
    client = GoogleSheetsClient()

    if client.worksheet:
        import_leads_to_database(client, './leads.db')


def quick_export():
    """Quick export: Push new database leads to Google Sheets"""
    print("🚀 Starting export to Google Sheets...")
    client = GoogleSheetsClient()

    if client.worksheet:
        export_new_leads_to_sheets(client, './leads.db')


if __name__ == "__main__":
    print("=" * 60)
    print("LeadForge AI - Google Sheets Integration")
    print("=" * 60)
    print("\nChoose an option:")
    print("1. Import leads from Google Sheets to database")
    print("2. Export new database leads to Google Sheets")
    print("3. Both (sync)")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ")

    if choice == '1':
        quick_import()
    elif choice == '2':
        quick_export()
    elif choice == '3':
        quick_import()
        quick_export()
    else:
        print("Goodbye!")
