#!/usr/bin/env python3
"""
Automated Import Script - No user input required
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from google_sheets_integration import GoogleSheetsClient, import_leads_to_database
from main import DB_PATH

def main():
    print("=" * 70)
    print("🚀 LeadForge AI - Google Sheets Import")
    print("=" * 70)
    print()
    print("📋 Importing your 527 leads from Google Sheets")
    print("   into the LeadForge database...")
    print()

    # Initialize client
    client = GoogleSheetsClient()

    if not client.worksheet:
        print()
        print("❌ Failed to connect to Google Sheets")
        print()
        print("📋 Troubleshooting:")
        print("   1. Check that credentials.json exists in this directory")
        print("   2. A browser window should open for authentication")
        print("   3. Authorize the app when prompted")
        print()
        return

    print()
    print("📊 Reading leads from Google Sheet...")

    # Read leads
    leads = client.read_all_leads()

    if not leads:
        print("❌ No leads found in Google Sheet")
        return

    print(f"✅ Found {len(leads)} leads in your Google Sheet")
    print()
    print("📥 Importing leads to LeadForge database...")
    print()

    # Import to database
    imported_count = import_leads_to_database(client, DB_PATH)

    print()
    print("=" * 70)
    print("🎉 Import Complete!")
    print("=" * 70)
    print()
    print(f"✅ Successfully imported {imported_count} leads")
    print()
    print("📊 Your leads are now available in:")
    print(f"   • Database: {DB_PATH}")
    print("   • LeadForge Dashboard: http://localhost:8000")
    print()

if __name__ == "__main__":
    main()
