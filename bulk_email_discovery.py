#!/usr/bin/env python3
"""
Bulk Email Discovery for all Google Sheets leads
"""

import requests
import json
import time
from typing import List, Dict

# API endpoint
API_BASE = "http://localhost:8000"

def bulk_discover_emails(domains: List[str], companies: List[str] = None, batch_size: int = 5):
    """
    Discover emails for multiple domains in batches

    Args:
        domains: List of domains to search
        companies: Optional list of company names
        batch_size: Number of domains to process per batch
    """
    results = {
        'total_domains': len(domains),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_emails_found': 0,
        'domains_with_emails': 0,
        'results': {}
    }

    print("=" * 60)
    print("📧 Bulk Email Discovery")
    print("=" * 60)
    print(f"📊 Total domains to process: {len(domains)}")
    print(f"🔢 Batch size: {batch_size}")
    print("=" * 60)

    for i in range(0, len(domains), batch_size):
        batch_domains = domains[i:i+batch_size]
        batch_companies = companies[i:i+batch_size] if companies else [None] * len(batch_domains)

        print(f"\n🔄 Processing batch {i//batch_size + 1} (domains {i+1}-{min(i+batch_size, len(domains))})...")

        # Prepare request
        request_data = {
            "domains": batch_domains,
            "companies": batch_companies
        }

        try:
            # Call bulk email discovery API
            response = requests.post(
                f"{API_BASE}/api/bulk-email-discover",
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    # Process results
                    batch_results = data.get('results', {})

                    for domain, emails in batch_results.items():
                        results['results'][domain] = emails
                        results['processed'] += 1

                        if emails:
                            results['successful'] += 1
                            results['total_emails_found'] += len(emails)
                            results['domains_with_emails'] += 1
                            print(f"   ✅ {domain}: {len(emails)} emails found")
                        else:
                            results['failed'] += 1
                            print(f"   ⚠️  {domain}: No emails found")
                else:
                    print(f"   ❌ Batch failed: {data.get('error', 'Unknown error')}")
                    results['failed'] += len(batch_domains)
            else:
                print(f"   ❌ API error: {response.status_code}")
                results['failed'] += len(batch_domains)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results['failed'] += len(batch_domains)

        # Rate limiting - wait between batches
        if i + batch_size < len(domains):
            print(f"   ⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)

    # Save results
    with open('email_discovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Email Discovery Summary")
    print("=" * 60)
    print(f"✅ Processed: {results['processed']}/{results['total_domains']} domains")
    print(f"📧 Successful: {results['successful']} domains")
    print(f"❌ Failed: {results['failed']} domains")
    print(f"🎯 Domains with emails: {results['domains_with_emails']}")
    print(f"📊 Total emails found: {results['total_emails_found']}")
    print(f"💾 Results saved to: email_discovery_results.json")
    print("=" * 60)

    return results

if __name__ == "__main__":
    import sys

    # Option 1: Load from domains file
    try:
        with open('domains_for_email_discovery.json', 'r') as f:
            data = json.load(f)
            domains = data['domains']
            companies = data.get('companies', [])
    except FileNotFoundError:
        print("❌ domains_for_email_discovery.json not found")
        print("💡 Run extract_domains.py first to generate this file")
        sys.exit(1)

    # Option 2: Test with sample domains
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        domains = ['apple.com', 'microsoft.com', 'google.com']
        companies = ['Apple', 'Microsoft', 'Google']
        print("🧪 Running in TEST mode with 3 domains")

    # Run bulk discovery
    bulk_discover_emails(domains, companies, batch_size=5)
