#!/usr/bin/env python3
"""
Google Sheets Sync Module - Sync database changes back to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import sqlite3
from datetime import datetime

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "Imported Leads Clean"
SERVICE_ACCOUNT_FILE = 'service_account.json'
DB_PATH = 'leads.db'

class GoogleSheetsSync:
    def __init__(self):
        self.sheet = None
        self.worksheet = None
        self.headers = []
        self._connect()

    def _connect(self):
        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
            client = gspread.authorize(creds)
            self.sheet = client.open_by_key(SHEET_ID)
            self.worksheet = self.sheet.worksheet(WORKSHEET_NAME)
            self.headers = self.worksheet.row_values(1)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def _get_column_letter(self, col_index):
        col_index += 1
        if col_index <= 26:
            return chr(64 + col_index)
        else:
            return chr(64 + (col_index - 1) // 26) + chr(65 + (col_index - 1) % 26)

    def _find_column(self, column_name):
        try:
            if column_name in self.headers:
                return self.headers.index(column_name)
            return None
        except:
            return None

    def sync_emails_to_sheets(self, limit=None):
        print("🔄 Syncing Emails to Google Sheets")
        
        if not self.worksheet:
            if not self._connect():
                return {"success": False, "error": "Connection failed"}

        try:
            all_data = self.worksheet.get_all_values()
            data_rows = all_data[1:]
            
            company_col_idx = 0
            email_col_idx = self._find_column('Email')
            
            if email_col_idx is None:
                return {"success": False, "error": "Email column not found"}
            
            email_col_letter = self._get_column_letter(email_col_idx)
            print(f"Email column: {email_col_letter}")
            
            sheet_map = {}
            for i, row in enumerate(data_rows, start=2):
                company_name = row[company_col_idx] if company_col_idx < len(row) else ""
                if company_name:
                    sheet_map[company_name.lower().strip()] = {
                        'row': i,
                        'current_email': row[email_col_idx] if email_col_idx < len(row) else ""
                    }
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            query = 'SELECT id, business_name, email FROM leads WHERE email IS NOT NULL AND email != ""'
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            db_leads = cursor.fetchall()
            conn.close()
            
            print(f"Found {len(db_leads)} leads with emails")
            
            updates = []
            for lead_id, business_name, email in db_leads:
                company_key = business_name.lower().strip()
                if company_key in sheet_map:
                    sheet_info = sheet_map[company_key]
                    if sheet_info['current_email'] != email:
                        updates.append({
                            'row': sheet_info['row'],
                            'business_name': business_name,
                            'email': email
                        })
            
            print(f"Updating {len(updates)} leads")
            
            updated = 0
            for update in updates:
                try:
                    cell = f"{email_col_letter}{update['row']}"
                    self.worksheet.update([[update['email']]], cell)
                    updated += 1
                except Exception as e:
                    print(f"Error: {e}")
            
            return {
                "success": True,
                "synced": updated,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def sync_emails(limit=None):
    sync = GoogleSheetsSync()
    return sync.sync_emails_to_sheets(limit=limit)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    result = sync_emails(limit)
    print(f"Result: {result}")
