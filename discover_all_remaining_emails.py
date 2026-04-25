#!/usr/bin/env python3
"""
Discover emails for ALL remaining leads that have websites but no emails
"""

import sqlite3
import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:8000'
DB_PATH = 'leads.db'

def discover_all_remaining_emails():
    """Discover emails for all leads with websites but no emails"""

    print("=" * 60)
    print("🔍 Email Discovery for ALL Remaining Leads")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find all leads with websites but no emails
    cursor.execute('''
        SELECT id, business_name, website, score
        FROM leads
        WHERE website IS NOT NULL
        AND website != ''
        AND (email IS NULL OR email = '')
        ORDER BY score DESC
    ''')

    leads = cursor.fetchall()
    conn.close()

    if not leads:
        print("\n✅ All leads already have emails!")
        return

    print(f"\n📊 Found {len(leads)} leads that need email discovery")
    print("=" * 60)

    # Process in batches of 25 to save API credits
    batch_size = 25
    total_batches = (len(leads) + batch_size - 1) // batch_size

    print(f"\n🔄 Will process in {total_batches} batches of {batch_size} leads")
    print(f"   (This will use {total_batches} Hunter.io API searches)")
    print(f"   Free tier: 25 searches/month")
    print("=" * 60)

    # Ask for confirmation
    if total_batches > 1:
        print(f"\n⚠️  WARNING: This will use {total_batches} Hunter.io API searches")
        print(f"   Free tier remaining: ~{25 - 11} searches (already used 11)")
        print(f"\n💡 Recommendation: Process 1 batch (25 leads) to stay within free tier")
        print(f"   Or upgrade to $49/month for 1,000 searches")

        choice = input("\nContinue? (yes/no/recommend): ").strip().lower()

        if choice == 'recommend':
            batch_size = 14  # Use remaining free credits
            print(f"\n✅ Processing {batch_size} leads to stay within free tier")
        elif choice != 'yes':
            print("\n❌ Cancelled")
            return

    # Process batches
    total_updated = 0
    total_emails_found = 0
    processed_leads = 0

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(leads))
        batch_leads = leads[start_idx:end_idx]

        print(f"\n{'=' * 60}")
        print(f"🔄 Batch {batch_num + 1}/{total_batches} (Leads {start_idx + 1}-{end_idx})")
        print('=' * 60)

        # Extract domains
        domains = []
        companies = []
        lead_mapping = {}

        for lead_id, business_name, website, score in batch_leads:
            # Extract domain from website
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

            if domain:
                domains.append(domain)
                companies.append(business_name)
                lead_mapping[domain] = {
                    'id': lead_id,
                    'business_name': business_name,
                    'website': website,
                    'score': score
                }

        if not domains:
            print("   ⚠️  No valid domains in this batch")
            continue

        # Call bulk email discovery API
        try:
            print(f"   🔍 Discovering emails for {len(domains)} domains...")
            response = requests.post(
                f"{API_BASE}/api/bulk-email-discover",
                json={"domains": domains, "companies": companies},
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    batch_emails_found = data.get('total_emails_found', 0)
                    domains_with_emails = data.get('domains_with_emails', 0)
                    results = data.get('results', {})

                    print(f"   ✅ Found {batch_emails_found} emails for {domains_with_emails} domains")

                    # Update database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()

                    batch_updated = 0

                    for domain, emails in results.items():
                        if emails and len(emails) > 0:
                            lead_info = lead_mapping.get(domain)
                            if lead_info:
                                # Get the best email
                                primary_email = emails[0]
                                email_address = primary_email.get('email', '')
                                confidence = primary_email.get('confidence_score', 0)

                                if email_address:
                                    # Update lead
                                    cursor.execute(
                                        'UPDATE leads SET email = ? WHERE id = ?',
                                        (email_address, lead_info['id'])
                                    )
                                    batch_updated += 1

                                    # Show progress
                                    print(f"      ✅ {lead_info['business_name'][:40]:40s}")
                                    print(f"         Email: {email_address}")
                                    print(f"         Confidence: {confidence}%")

                    conn.commit()
                    conn.close()

                    total_updated += batch_updated
                    total_emails_found += batch_emails_found
                    processed_leads += len(batch_leads)

                    print(f"   📝 Updated {batch_updated} leads in database")

                    # Rate limiting - wait between batches
                    if batch_num < total_batches - 1:
                        print(f"   ⏳ Waiting 2 seconds before next batch...")
                        import time
                        time.sleep(2)

            else:
                print(f"   ❌ API error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 Email Discovery Complete!")
    print("=" * 60)
    print(f"✅ Processed: {processed_leads} leads")
    print(f"✅ Updated: {total_updated} leads with emails")
    print(f"✅ Total emails found: {total_emails_found}")
    print("=" * 60)

    # Export results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_processed': processed_leads,
        'leads_updated': total_updated,
        'total_emails_found': total_emails_found,
        'batches_processed': total_batches
    }

    with open('all_email_discovery_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved: all_email_discovery_results.json")

    # Export updated leads to CSV
    print("\n📥 Exporting updated leads to CSV...")
    import subprocess
    subprocess.run(['python3', 'export_leads_with_emails.py'])

if __name__ == "__main__":
    discover_all_remaining_emails()
