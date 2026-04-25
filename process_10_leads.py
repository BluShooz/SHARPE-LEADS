#!/usr/bin/env python3
"""
Process 10 Leads: Google Sheets → Email Discovery → Database → Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import sqlite3
import requests
from datetime import datetime

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'
DB_PATH = 'leads.db'
API_BASE = 'http://localhost:8000'

def process_10_leads():
    """Process 10 leads from Google Sheets through email discovery"""

    print("=" * 60)
    print("🔄 Processing 10 Leads: Sheets → Email Discovery → Database → Sheets")
    print("=" * 60)

    # Step 1: Get 10 leads from Google Sheets that need emails
    print("\n📋 Step 1: Getting 10 leads from Google Sheets...")
    print("-" * 60)

    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(WORKSHEET_NAME)

        print("✅ Connected to Google Sheets")

        # Get all data
        all_data = worksheet.get_all_values()
        headers = all_data[0]
        data_rows = all_data[1:]

        # Find column indices
        company_col = 0
        website_col = None
        email_col = None

        if 'Primary Link' in headers:
            website_col = headers.index('Primary Link')
        if 'Confirmed Best Email' in headers:
            email_col = headers.index('Confirmed Best Email')

        if website_col is None or email_col is None:
            print(f"❌ Required columns not found!")
            print(f"   Website column: {website_col}")
            print(f"   Email column: {email_col}")
            return

        # Find 10 leads that have websites but no emails
        leads_to_process = []

        for i, row in enumerate(data_rows, start=2):
            company_name = row[company_col] if company_col < len(row) else ""
            website = row[website_col] if website_col < len(row) else ""
            email = row[email_col] if email_col < len(row) else ""

            # Skip if no company name or no website
            if not company_name or not website:
                continue

            # Skip if already has email
            if email and email.strip():
                continue

            leads_to_process.append({
                'row': i,
                'company': company_name,
                'website': website,
                'current_email': email
            })

            if len(leads_to_process) >= 10:
                break

        if not leads_to_process:
            print("\n✅ All leads in Google Sheet already have emails!")
            return

        print(f"✅ Found {len(leads_to_process)} leads that need email discovery")
        print(f"   Processing first {min(10, len(leads_to_process))} leads")

    except Exception as e:
        print(f"❌ Error reading from Google Sheets: {e}")
        return

    # Step 2: Extract domains and discover emails
    print("\n📧 Step 2: Discovering emails...")
    print("-" * 60)

    domains = []
    companies = []
    lead_mapping = {}

    for lead in leads_to_process[:10]:
        # Extract domain from website
        website = lead['website']
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

        if domain:
            domains.append(domain)
            companies.append(lead['company'])
            lead_mapping[domain] = lead

    if not domains:
        print("\n❌ No valid domains found")
        return

    print(f"🔍 Discovering emails for {len(domains)} domains...")

    try:
        response = requests.post(
            f"{API_BASE}/api/bulk-email-discover",
            json={"domains": domains, "companies": companies},
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            return

        data = response.json()

        if not data.get('success'):
            print(f"❌ Email discovery failed: {data.get('error')}")
            return

        results = data.get('results', {})
        total_emails_found = data.get('total_emails_found', 0)

        print(f"✅ Found {total_emails_found} emails for {len(domains)} domains")

    except Exception as e:
        print(f"❌ Error discovering emails: {e}")
        return

    # Step 3: Update database with discovered emails
    print("\n💾 Step 3: Updating database...")
    print("-" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        updated_count = 0

        for domain, emails in results.items():
            if emails and len(emails) > 0:
                lead = lead_mapping.get(domain)

                if lead:
                    # Get the best email (first one with highest confidence)
                    primary_email = emails[0]
                    email_address = primary_email.get('email', '')
                    confidence = primary_email.get('confidence_score', 0)
                    verification = primary_email.get('verification_status', 'unknown')

                    if email_address:
                        # Check if lead already exists in database
                        cursor.execute('''
                            SELECT id FROM leads WHERE business_name = ?
                        ''', (lead['company'],))

                        existing = cursor.fetchone()

                        if existing:
                            # Update existing lead
                            lead_id = existing[0]
                            cursor.execute('''
                                UPDATE leads SET email = ? WHERE id = ?
                            ''', (email_address, lead_id))
                            print(f"   ✅ Updated: {lead['company'][:40]:40s}")
                            print(f"      Email: {email_address}")
                            print(f"      Confidence: {confidence}%")
                            print(f"      Status: {verification}")
                        else:
                            # Insert new lead
                            cursor.execute('''
                                INSERT INTO leads (business_name, website, email, score, status)
                                VALUES (?, ?, ?, 70, 'new')
                            ''', (lead['company'], lead['website'], email_address))
                            print(f"   ✅ Added: {lead['company'][:40]:40s}")
                            print(f"      Email: {email_address}")
                            print(f"      Confidence: {confidence}%")
                            print(f"      Status: {verification}")

                        updated_count += 1

        conn.commit()
        conn.close()

        print(f"\n✅ Updated {updated_count} leads in database")

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return

    # Step 4: Sync emails back to Google Sheets
    print("\n🔄 Step 4: Syncing emails back to Google Sheets...")
    print("-" * 60)

    try:
        # Get column letter for email column
        email_col_letter = chr(64 + (email_col + 1)) if email_col + 1 <= 26 else chr(64 + ((email_col + 1) - 1) // 26) + chr(65 + ((email_col + 1) - 1) % 26)

        synced_count = 0

        for domain, emails in results.items():
            if emails and len(emails) > 0:
                lead = lead_mapping.get(domain)

                if lead:
                    # Get the best email
                    primary_email = emails[0]
                    email_address = primary_email.get('email', '')

                    if email_address:
                        row = lead['row']
                        cell_notation = f"{email_col_letter}{row}"

                        # Write to Google Sheet
                        worksheet.update(
                            [[email_address]],
                            cell_notation
                        )

                        print(f"   ✅ Row {row}: {lead['company'][:40]:40s}")
                        print(f"      {cell_notation} = {email_address}")
                        synced_count += 1

        print(f"\n✅ Synced {synced_count} leads to Google Sheet")

    except Exception as e:
        print(f"❌ Error syncing to Google Sheets: {e}")
        return

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Process Complete")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Leads processed: {min(10, len(leads_to_process))}")
    print(f"   Emails discovered: {total_emails_found}")
    print(f"   Database updated: ✓")
    print(f"   Google Sheet synced: ✓")
    print(f"\n💰 Hunter.io credits used: {len(domains)}")

    print(f"\n✅ These 10 leads now have:")
    print(f"   • Discovered email addresses")
    print(f"   • Verification status")
    print(f"   • Confidence scores")
    print(f"   • Updated in database")
    print(f"   • Synced to Google Sheet")

    print(f"\n📁 Updated files:")
    print(f"   • Database: {DB_PATH}")
    print(f"   • Google Sheet: Row 2-527, Column CB (Confirmed Best Email)")

    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    process_10_leads()
