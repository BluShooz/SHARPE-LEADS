#!/usr/bin/env python3
"""
Direct Email Discovery to Google Sheets
No local database - writes directly to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "Imported Leads Clean"  # Master database with no duplicates
SERVICE_ACCOUNT_FILE = '/Users/jonsmith/leadforge-scraper/service_account.json'
HUNTER_API_KEY = "17aaebe1a4244027b283e2c40c2c3dd2f9b9b10c"

class DirectEmailDiscovery:
    """Discover emails and write directly to Google Sheets"""
    
    def __init__(self):
        self.sheet = None
        self.worksheet = None
        self.headers = []
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets"""
        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
            client = gspread.authorize(creds)
            self.sheet = client.open_by_key(SHEET_ID)
            self.worksheet = self.sheet.worksheet(WORKSHEET_NAME)
            self.headers = self.worksheet.row_values(1)
            print("✅ Connected to Google Sheets")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def _get_column_letter(self, col_index):
        """Convert column index to letter"""
        col_index += 1
        if col_index <= 26:
            return chr(64 + col_index)
        else:
            return chr(64 + (col_index - 1) // 26) + chr(65 + (col_index - 1) % 26)
    
    def _find_column(self, column_name):
        """Find column by name"""
        if column_name in self.headers:
            return self.headers.index(column_name)
        return None
    
    def discover_email_for_domain(self, domain, company_name):
        """Discover email for a single domain"""
        try:
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'api_key': HUNTER_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('data', {}).get('emails', [])
                
                if emails:
                    # Return the highest confidence email
                    best_email = max(emails, key=lambda x: x.get('confidence', 0))
                    return {
                        'success': True,
                        'email': best_email.get('value'),
                        'confidence': best_email.get('confidence'),
                        'name': best_email.get('first_name') + ' ' + best_email.get('last_name') if best_email.get('first_name') else '',
                        'position': best_email.get('position', '')
                    }
            
            return {'success': False, 'error': 'No email found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_and_update_email(self, row_number, company_name, website):
        """Find email and update Google Sheet directly"""
        
        if not self.worksheet:
            if not self._connect():
                return {'success': False, 'error': 'Not connected to Sheets'}
        
        print(f"🔍 Processing row {row_number}: {company_name}")
        
        # Extract domain from website
        if not website or website == 'N/A':
            return {'success': False, 'error': 'No website available'}
        
        # Clean website URL to get domain
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        # Discover email
        result = self.discover_email_for_domain(domain, company_name)
        
        if not result['success']:
            print(f"   ❌ {result.get('error', 'Unknown error')}")
            return result
        
        # Find email column
        email_col_idx = self._find_column('Email')
        if not email_col_idx:
            return {'success': False, 'error': 'Email column not found'}
        
        email_col_letter = self._get_column_letter(email_col_idx)
        cell_notation = f"{email_col_letter}{row_number}"
        
        # Update Google Sheet directly
        try:
            self.worksheet.update([[result['email']]], cell_notation)
            print(f"   ✅ Updated {cell_notation} with {result['email']}")
            
            return {
                'success': True,
                'row': row_number,
                'company': company_name,
                'email': result['email'],
                'confidence': result['confidence'],
                'cell': cell_notation
            }
        
        except Exception as e:
            print(f"   ❌ Update failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_leads_without_emails(self, limit=10):
        """Process leads that don't have emails yet"""
        
        if not self._connect():
            return {'success': False, 'error': 'Connection failed'}
        
        try:
            # Get all data from sheet
            all_data = self.worksheet.get_all_values()
            headers = all_data[0]
            data_rows = all_data[1:]
            
            # Find columns
            company_col_idx = 0  # Column A - Business Name
            website_col_idx = self._find_column('Website')
            email_col_idx = self._find_column('Email')
            
            if not website_col_idx or not email_col_idx:
                return {'success': False, 'error': 'Required columns not found'}
            
            # Find rows without emails
            rows_to_process = []
            
            for i, row in enumerate(data_rows[:limit], start=2):
                if len(row) > max(company_col_idx, website_col_idx, email_col_idx):
                    company = row[company_col_idx] if company_col_idx < len(row) else ""
                    website = row[website_col_idx] if website_col_idx < len(row) else ""
                    email = row[email_col_idx] if email_col_idx < len(row) else ""
                    
                    # Process if company exists, website exists, but no email
                    if company and website and not email:
                        rows_to_process.append({
                            'row': i,
                            'company': company,
                            'website': website
                        })
            
            print(f"\n📊 Found {len(rows_to_process)} leads without emails")
            print(f"🔄 Processing {min(limit, len(rows_to_process))} leads...\n")
            
            # Process each lead
            results = []
            for lead in rows_to_process[:limit]:
                result = self.find_and_update_email(
                    lead['row'],
                    lead['company'],
                    lead['website']
                )
                results.append(result)
            
            # Count successes
            successful = sum(1 for r in results if r['success'])
            
            print(f"\n{'='*60}")
            print(f"✅ Processed {len(results)} leads")
            print(f"✅ Successfully discovered {successful} emails")
            print(f"{'='*60}")
            
            return {
                'success': True,
                'processed': len(results),
                'successful': successful,
                'results': results
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """Main function"""
    import sys
    
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print("="*60)
    print("🔍 Direct Email Discovery to Google Sheets")
    print("="*60)
    
    discovery = DirectEmailDiscovery()
    result = discovery.process_leads_without_emails(limit=limit)
    
    print(f"\n📊 Final Result: {result}")


if __name__ == "__main__":
    main()
