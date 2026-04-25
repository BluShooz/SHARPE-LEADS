#!/usr/bin/env python3
"""
Extract domains from Google Sheets leads for bulk email discovery
"""

from google_sheets_integration import GoogleSheetsClient
import json

def extract_domains_from_leads():
    """Extract unique domains from Google Sheets leads"""
    try:
        print("🔍 Loading leads from Google Sheets...")
        client = GoogleSheetsClient()
        leads = client.read_all_leads()

        print(f"✅ Loaded {len(leads)} leads")

        # Extract unique domains
        domains = []
        lead_companies = {}

        for lead in leads:
            website = lead.get('website', '')
            company = lead.get('business_name', '')

            if website and company:
                # Extract domain from URL
                domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

                if domain and domain not in lead_companies:
                    domains.append(domain)
                    lead_companies[domain] = company

        print(f"\n📊 Found {len(domains)} unique domains:")
        for i, domain in enumerate(domains[:20], 1):
            print(f"   {i}. {domain} ({lead_companies[domain]})")

        if len(domains) > 20:
            print(f"   ... and {len(domains) - 20} more")

        # Save to file for bulk processing
        output = {
            'total_domains': len(domains),
            'domains': domains,
            'companies': [lead_companies.get(d, '') for d in domains]
        }

        with open('domains_for_email_discovery.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Saved to domains_for_email_discovery.json")
        print(f"\n💡 Next step: Run bulk email discovery with these domains")

        return domains, [lead_companies.get(d, '') for d in domains]

    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

if __name__ == "__main__":
    extract_domains_from_leads()
