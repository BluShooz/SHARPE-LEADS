"""
LeadForge AI - Enhanced Google Sheets Sync
Automatically syncs all generated leads with verified information to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

class AutoSheetsSync:
    """Automatic Google Sheets synchronization for all generated leads"""

    def __init__(self):
        self.client = None
        self.sheet = None
        self.worksheet = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization - only connect when needed"""
        if self._initialized:
            return True

        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(SHEET_ID)
            self.worksheet = self.sheet.worksheet(WORKSHEET_NAME)
            self._initialized = True
            print("✅ Google Sheets sync ready")
            return True
        except Exception as e:
            print(f"⚠️  Google Sheets sync unavailable: {e}")
            return False

    def sync_leads_to_sheets(self, leads: List[Dict]) -> int:
        """
        Sync all generated leads to Google Sheets with full verified information

        Args:
            leads: List of lead dictionaries with all verified data

        Returns:
            Number of leads successfully synced
        """
        if not leads:
            return 0

        if not self._ensure_initialized():
            return 0

        synced_count = 0

        for lead in leads:
            try:
                # Prepare row with all verified information
                row = self._prepare_lead_row(lead)

                # Check for duplicates first
                if self._is_duplicate(lead):
                    # Update existing lead instead
                    self._update_existing_lead(lead, row)
                    print(f"🔄 Updated: {lead.get('business_name', 'Unknown')}")
                else:
                    # Add new lead
                    self.worksheet.append_row(row)
                    print(f"✅ Synced: {lead.get('business_name', 'Unknown')} - {lead.get('city', 'N/A')}, {lead.get('state', 'N/A')}")

                synced_count += 1

            except Exception as e:
                print(f"⚠️  Sync failed for {lead.get('business_name', 'Unknown')}: {e}")

        return synced_count

    def _prepare_lead_row(self, lead: Dict) -> List:
        """
        Prepare lead data for Google Sheets with all verified information

        Columns order:
        Company, Primary Link, Phone, City, State, County, Industry,
        Rating, Reviews, Score, Address, Latitude, Longitude,
        Verified Location, Date Added
        """
        return [
            lead.get('business_name', ''),                    # Company
            lead.get('website', ''),                          # Primary Link
            lead.get('phone', ''),                            # Phone
            lead.get('city', lead.get('location', '')),      # City
            lead.get('state', ''),                            # State
            lead.get('county', ''),                           # County
            lead.get('industry', ''),                         # Industry
            lead.get('rating', ''),                           # Rating
            lead.get('reviews_count', ''),                    # Reviews
            lead.get('score', ''),                            # Score
            lead.get('address', ''),                          # Address
            lead.get('latitude', ''),                         # Latitude
            lead.get('longitude', ''),                        # Longitude
            'YES' if lead.get('verified_location') else 'NO', # Verified Location
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')     # Date Added
        ]

    def _is_duplicate(self, lead: Dict) -> bool:
        """Check if lead already exists in sheet"""
        try:
            # Get all rows
            all_data = self.worksheet.get_all_values()

            if not all_data or len(all_data) < 2:
                return False

            # Skip header row
            for row in all_data[1:]:
                if len(row) > 0 and row[0] == lead.get('business_name', ''):
                    return True

            return False

        except Exception:
            return False

    def _update_existing_lead(self, lead: Dict, new_row: List):
        """Update existing lead with verified information"""
        try:
            all_data = self.worksheet.get_all_values()

            for i, row in enumerate(all_data[1:], start=2):  # Skip header, start at row 2
                if len(row) > 0 and row[0] == lead.get('business_name', ''):
                    # Update the row
                    cell_range = f"A{i}:{chr(65 + len(new_row) - 1)}{i}"
                    self.worksheet.update(cell_range, [new_row])
                    return

        except Exception as e:
            print(f"⚠️  Update failed: {e}")

    def sync_from_database(self, db_path: str = "leads.db", limit: int = 100) -> int:
        """
        Sync latest leads from database to Google Sheets

        Args:
            db_path: Path to SQLite database
            limit: Maximum number of leads to sync

        Returns:
            Number of leads synced
        """
        if not self._ensure_initialized():
            return 0

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get latest leads with all verified information
            cursor.execute('''
                SELECT id, business_name, industry, location, state, city, county,
                       phone, website, rating, reviews_count, address,
                       latitude, longitude, score, status, verified_location
                FROM leads
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()

            if not rows:
                conn.close()
                return 0

            leads = []
            for row in rows:
                lead = dict(row)
                leads.append(lead)

            conn.close()

            # Sync to sheets
            synced = self.sync_leads_to_sheets(leads)

            print(f"✅ Synced {synced}/{len(leads)} leads from database to Google Sheets")
            return synced

        except Exception as e:
            print(f"❌ Database sync error: {e}")
            return 0

    def get_sheet_stats(self) -> Dict:
        """Get statistics from Google Sheets"""
        if not self._ensure_initialized():
            return {}

        try:
            all_data = self.worksheet.get_all_values()

            return {
                'total_rows': len(all_data) - 1,  # Exclude header
                'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {'error': str(e)}


# Singleton instance for automatic sync
_auto_sync_instance = None

def get_auto_sync() -> AutoSheetsSync:
    """Get or create auto sync instance"""
    global _auto_sync_instance
    if _auto_sync_instance is None:
        _auto_sync_instance = AutoSheetsSync()
    return _auto_sync_instance


def auto_sync_leads(leads: List[Dict]) -> int:
    """
    Automatically sync leads to Google Sheets after generation

    This function is called automatically every time leads are generated
    to ensure Google Sheets is always up-to-date with all verified information.

    Args:
        leads: List of lead dictionaries

    Returns:
        Number of leads successfully synced
    """
    sync = get_auto_sync_instance()
    return sync.sync_leads_to_sheets(leads)


def auto_sync_from_database(db_path: str = "leads.db", limit: int = 100) -> int:
    """
    Automatically sync latest database leads to Google Sheets

    Args:
        db_path: Path to database
        limit: Maximum leads to sync

    Returns:
        Number of leads synced
    """
    sync = get_auto_sync_instance()
    return sync.sync_from_database(db_path, limit)
