#!/usr/bin/env python3
"""
Discover emails for all existing leads in the database
"""

import sqlite3
import os
import requests
import json
from datetime import datetime

# Configuration
DB_PATH = 'leads.db'
API_BASE = 'http://localhost:8000'

def discover_emails_for_existing_leads():
    """Discover emails for all leads that have websites but no emails"""

    print("=" * 60)
    print("🔍 Email Discovery for Existing Leads")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find leads with websites but no emails
    cursor.execute('''
        SELECT id, business_name, website
        FROM leads
        WHERE website IS NOT NULL
        AND website != ''
        AND (email IS NULL OR email = '')
        ORDER BY score DESC
        LIMIT 25
    ''')

    leads = cursor.fetchall()
    conn.close()

    if not leads:
        print("\n❌ No leads found that need email discovery")
        print("   All leads already have emails!")
        return

    print(f"\n📊 Found {len(leads)} leads that need email discovery")
    print(f"   (Processing top 25 by score to save API credits)")
    print("=" * 60)

    # Extract domains
    domains = []
    companies = []
    lead_mapping = {}

    for lead_id, business_name, website in leads:
        # Extract domain from website
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

        if domain:
            domains.append(domain)
            companies.append(business_name)
            lead_mapping[domain] = {
                'id': lead_id,
                'business_name': business_name,
                'website': website
            }

    if not domains:
        print("\n❌ No valid domains found")
        return

    print(f"\n🔍 Discovering emails for {len(domains)} domains...")
    print("=" * 60)

    # Call bulk email discovery API
    try:
        response = requests.post(
            f"{API_BASE}/api/bulk-email-discover",
            json={"domains": domains, "companies": companies},
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                total_emails = data.get('total_emails_found', 0)
                domains_with_emails = data.get('domains_with_emails', 0)

                print(f"\n✅ Email Discovery Complete!")
                print(f"   Domains processed: {len(domains)}")
                print(f"   Domains with emails: {domains_with_emails}")
                print(f"   Total emails found: {total_emails}")
                print("=" * 60)

                # Update database with discovered emails
                results = data.get('results', {})
                updated_count = 0
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                print(f"\n📝 Updating database with discovered emails...")
                print("=" * 60)

                for domain, emails in results.items():
                    if emails and len(emails) > 0:
                        lead_info = lead_mapping.get(domain)
                        if lead_info:
                            # Get the best email (first one with highest confidence)
                            primary_email = emails[0]
                            email_address = primary_email.get('email', '')
                            confidence = primary_email.get('confidence_score', 0)
                            verification = primary_email.get('verification_status', 'unknown')

                            if email_address:
                                # Update lead
                                cursor.execute(
                                    'UPDATE leads SET email = ? WHERE id = ?',
                                    (email_address, lead_info['id'])
                                )
                                updated_count += 1

                                print(f"   ✅ {lead_info['business_name']}")
                                print(f"      Email: {email_address}")
                                print(f"      Confidence: {confidence}%")
                                print(f"      Status: {verification}")
                                print(f"      Domain: {domain}")

                conn.commit()
                conn.close()

                print("=" * 60)
                print(f"\n✅ Updated {updated_count} leads with email addresses!")
                print(f"✅ Database updated successfully!")
                print("=" * 60)

                # Export results
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'total_leads_processed': len(leads),
                    'leads_updated': updated_count,
                    'total_emails_found': total_emails,
                    'results': results
                }

                with open('email_discovery_results.json', 'w') as f:
                    json.dump(output, f, indent=2)

                print(f"\n💾 Results saved to: email_discovery_results.json")

                # Instructions for next steps
                print("\n" + "=" * 60)
                print("📋 Next Steps:")
                print("=" * 60)
                print("1. ✅ Database updated with discovered emails")
                print("2. 🔄 Sync updated leads to Google Sheets")
                print("3. 📥 Export CSV with email addresses")
                print("=" * 60)

            else:
                print(f"\n❌ Email discovery failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ API error: {response.status_code}")
            print(f"   {response.text}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    discover_emails_for_existing_leads()
