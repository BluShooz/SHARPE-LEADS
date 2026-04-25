#!/usr/bin/env python3
"""
Quick Import Script - Import your 527 Google Sheets leads into LeadForge
Run this after setting up credentials.json
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
    print("📋 This will import your 527 leads from Google Sheets")
    print("   into the LeadForge database.")
    print()
    print("⚠️  Make sure you've completed the setup:")
    print("   1. Created credentials.json file")
    print("   2. Shared your sheet with the service account email")
    print()
    print("=" * 70)
    print()

    # Ask for confirmation
    response = input("Ready to import? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Import cancelled.")
        return

    print()
    print("🔌 Connecting to Google Sheets...")

    # Initialize client
    client = GoogleSheetsClient()

    if not client.worksheet:
        print()
        print("❌ Failed to connect to Google Sheets")
        print()
        print("📋 Troubleshooting:")
        print("   1. Check that credentials.json exists in this directory")
        print("   2. Verify you've shared the sheet with service account email")
        print("   3. Ensure Google Sheets API is enabled")
        print()
        print("   See GOOGLE_SHEETS_SETUP.md for detailed instructions")
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
    print("🔄 To sync new leads back to Google Sheets:")
    print("   python export_to_google_sheets.py")
    print()

if __name__ == "__main__":
    main()
