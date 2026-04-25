#!/usr/bin/env python3
"""
Export leads with emails to CSV directly from database
"""

import sqlite3
import csv
from datetime import datetime

def export_leads_with_emails():
    """Export all leads with email addresses to CSV"""

    print("=" * 60)
    print("📥 Exporting Leads with Emails to CSV")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()

    # Get all leads with emails
    cursor.execute('''
        SELECT id, business_name, industry, location, phone, website,
               rating, reviews_count, address, email, score, status, created_at
        FROM leads
        WHERE email IS NOT NULL
        AND email != ''
        ORDER BY score DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\n❌ No leads with emails found")
        return

    print(f"\n📊 Found {len(rows)} leads with email addresses")
    print("=" * 60)

    # Generate CSV filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"leads_with_emails_{timestamp}.csv"

    # Write to CSV
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        header = [
            'ID', 'Business Name', 'Industry', 'Location', 'Phone', 'Website',
            'Rating', 'Reviews', 'Address', 'Email', 'Score', 'Status', 'Created At'
        ]
        writer.writerow(header)

        # Data rows
        for row in rows:
            writer.writerow(row)

    print(f"\n✅ Successfully exported {len(rows)} leads to CSV!")
    print(f"   Filename: {csv_filename}")
    print("=" * 60)

    print("\n📋 Exported Leads:")
    for i, row in enumerate(rows[:15], 1):
        print(f"   {i}. {row[1]}")  # Business name
        print(f"      Email: {row[9]}")  # Email
        print(f"      Score: {row[10]}")  # Score
        print()

    if len(rows) > 15:
        print(f"   ... and {len(rows) - 15} more")

    print("=" * 60)
    print(f"\n💾 CSV file saved: {csv_filename}")
    print("=" * 60)

    # Show file location
    import os
    full_path = os.path.abspath(csv_filename)
    print(f"\n📍 Full path: {full_path}")

    # Show summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    print(f"Total leads with emails: {len(rows)}")
    print(f"Average score: {sum(row[10] for row in rows) / len(rows):.1f}")

    # Count by status
    status_count = {}
    for row in rows:
        status = row[11]
        status_count[status] = status_count.get(status, 0) + 1

    print("\nLeads by status:")
    for status, count in status_count.items():
        print(f"   {status}: {count}")

    print("=" * 60)

if __name__ == "__main__":
    export_leads_with_emails()
