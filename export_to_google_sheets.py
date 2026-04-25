#!/usr/bin/env python3
"""
Quick Export Script - Export new LeadForge leads to Google Sheets
Run this after scraping new leads to sync them to your sheet
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from google_sheets_integration import GoogleSheetsClient, export_new_leads_to_sheets
from main import DB_PATH

def main():
    print("=" * 70)
    print("🚀 LeadForge AI - Export to Google Sheets")
    print("=" * 70)
    print()
    print("📋 This will export NEW leads from LeadForge database")
    print("   to your Google Sheet.")
    print()
    print("⚠️  Only leads with status='new' will be exported")
    print()
    print("=" * 70)
    print()

    # Ask for confirmation
    response = input("Ready to export? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Export cancelled.")
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
    print("📤 Exporting new leads to Google Sheet...")
    print()

    # Export to sheets
    exported_count = export_new_leads_to_sheets(client, DB_PATH)

    print()
    print("=" * 70)
    print("🎉 Export Complete!")
    print("=" * 70)
    print()
    print(f"✅ Successfully exported {exported_count} new leads")
    print()
    print("📊 Your leads are now in your Google Sheet:")
    print("   https://docs.google.com/spreadsheets/d/1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo/edit")
    print()

if __name__ == "__main__":
    main()
