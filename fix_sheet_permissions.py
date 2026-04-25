#!/usr/bin/env python3
"""
Fix Google Sheets Write Permissions
Guide to give your service account write access
"""

print("=" * 60)
print("🔧 Google Sheets Write Permission Fix")
print("=" * 60)

# Step 1: Get the service account email
try:
    import json
    with open('service_account.json', 'r') as f:
        service_account = json.load(f)

    service_account_email = service_account.get('client_email')

    print("\n✅ Step 1: Get Your Service Account Email")
    print("=" * 60)
    print(f"\n📧 Your Service Account Email:")
    print(f"   {service_account_email}")
    print("\n📋 Copy this email address - you'll need it!")

except Exception as e:
    print(f"\n❌ Error reading service account file: {e}")
    exit(1)

# Step 2: Instructions
print("\n\n✅ Step 2: Share Your Google Sheet")
print("=" * 60)
print("\n1. Open your Google Sheet:")
print(f"   https://docs.google.com/spreadsheets/d/1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo/edit")
print("\n2. Click the 'Share' button (top right)")
print("\n3. Paste this email:")
print(f"   {service_account_email}")
print("\n4. Set permission to 'Editor' (NOT Viewer)")
print("\n5. Click 'Send'")
print("\n6. Wait a few seconds for permissions to take effect")

# Step 3: Test the permissions
print("\n\n✅ Step 3: Test Write Permissions")
print("=" * 60)
print("\nAfter sharing, run this test:")

print("\n   python3 test_sheet_write.py")

print("\n\n💡 If you still get permission errors, also try:")
print("   1. Make sure the service account email doesn't have spaces")
print("   2. Try removing and re-adding the service account")
print("   3. Check that the service account email is exact (no typos)")

print("\n" + "=" * 60)
print("❓ Ready to test? (yes/no): ")

choice = input().strip().lower()

if choice == 'yes':
    print("\n🧪 Testing write permissions...")

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo")
        worksheet = sheet.worksheet("All Leads")

        # Try to write a test value
        test_cell = "A2"
        original_value = worksheet.acell(test_cell).value

        # Try to update
        worksheet.update(test_cell, [[original_value]])

        print("\n✅ SUCCESS! Write permissions are working!")
        print("   The service account can now write to your Google Sheet")

        # Test updating with email
        print("\n🧪 Testing email update...")

        # Find first row with empty email
        all_data = worksheet.get_all_records()
        updated_count = 0

        for i, row in enumerate(all_data[:5], 2):  # Test first 5 rows
            if not row.get('Confirmed Best Email', '').strip():
                # Try to update with test email
                worksheet.update(f'AK{i}', [[f'test{i}@example.com']])
                updated_count += 1
                print(f"   ✅ Updated row {i} with test email")

                if updated_count >= 2:
                    break

        print(f"\n✅ Successfully tested {updated_count} email updates")

    except Exception as e:
        print(f"\n❌ Permission test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you set permission to 'Editor' (not Viewer)")
        print("   2. Wait 30-60 seconds after sharing for permissions to sync")
        print("   3. Try removing and re-adding the service account")
        print("   4. Make sure you're sharing the RIGHT sheet (ID: 1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo)")

else:
    print("\n⏸️  Skipped test. Complete the sharing step first, then run:")
    print("   python3 fix_sheet_permissions.py")

print("\n" + "=" * 60)
