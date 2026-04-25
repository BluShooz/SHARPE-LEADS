# Google Sheets Sync System

## Overview

The LeadForge AI system now includes **bidirectional sync** with Google Sheets:

1. **Load from Sheets** → Pull leads from Google Sheets into the web app
2. **Email Discovery** → Find emails using Hunter.io API
3. **Sync to Sheets** → Push discovered emails back to Google Sheets ✅

---

## Features

### ✅ Automatic Sync After Email Discovery

When you click "🔍 Find All Emails" in the web app:
1. System discovers emails using Hunter.io API
2. **Automatically syncs** discovered emails to Google Sheets after 3 seconds
3. Shows toast notification: "🔄 Auto-synced X emails to Google Sheets!"

### ✅ Manual Sync Button

New button in the web app: **"🔄 Sync to Sheets"**
- Manually trigger sync of all discovered emails to Google Sheets
- Useful if auto-sync fails or you want to sync immediately

### ✅ API Endpoint

**POST** `/api/sync-to-sheets`

Request body:
```json
{
  "limit": 10  // Optional: Limit number of leads to sync
}
```

Response:
```json
{
  "success": true,
  "synced": 5,
  "timestamp": "2026-03-20T08:20:46.776366"
}
```

---

## How It Works

### 1. Database → Google Sheets

The sync system:
1. Reads all leads with emails from the SQLite database
2. Matches them to Google Sheet rows by company name
3. Updates the "Confirmed Best Email" column (Column CB)
4. Skips leads that already have the same email

### 2. Column Mapping

| Database Field | Google Sheet Column |
|----------------|---------------------|
| `business_name` | Column A (Business Name) |
| `email` | Column CB (Confirmed Best Email) |

### 3. Protected Cell Handling

The system automatically:
- Skips protected cells/rows
- Continues syncing unprotected rows
- Reports errors for any failed updates

---

## Command Line Usage

### Sync All Emails
```bash
cd /Users/jonsmith/leadforge-scraper
python3 sync_to_sheets.py
```

### Sync Limited Number of Emails
```bash
python3 sync_to_sheets.py 10  # Sync only 10 emails
```

### Auto-Sync Script
```bash
python3 auto_sync_emails.py
```

---

## API Integration Examples

### Using cURL
```bash
curl -X POST http://localhost:8000/api/sync-to-sheets \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

### Using JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:8000/api/sync-to-sheets', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({limit: 10})
});

const result = await response.json();
console.log(`Synced ${result.synced} emails`);
```

### Using Python
```python
import requests

response = requests.post(
    'http://localhost:8000/api/sync-to-sheets',
    json={'limit': 10}
)

result = response.json()
print(f"Synced {result['synced']} emails")
```

---

## Troubleshooting

### Issue: "Synced 0 emails"

**Cause**: All emails already synced to Google Sheet

**Solution**: 
- Check if database has emails: `sqlite3 leads.db "SELECT COUNT(*) FROM leads WHERE email IS NOT NULL"`
- If 0 emails, discover emails first using "🔍 Find All Emails" button

### Issue: "Email column not found"

**Cause**: Google Sheet doesn't have "Confirmed Best Email" column

**Solution**: 
- Add column named "Confirmed Best Email" to Google Sheet
- Or update column name in `sync_to_sheets.py`

### Issue: Protected cell errors

**Cause**: Google Sheet has protected cells/ranges

**Solution**: 
- Remove protection from Google Sheet
- Or skip protected rows (system does this automatically)

---

## File Structure

```
leadforge-scraper/
├── sync_to_sheets.py          # Core sync module
├── auto_sync_emails.py        # Auto-sync script
├── main.py                     # API server with /api/sync-to-sheets endpoint
└── GOOGLE_SHEETS_SYNC.md       # This documentation

Desktop/
└── leadforge-demo.html        # Frontend with sync button
```

---

## Current Status

✅ **Working Features:**
- Read from Google Sheets (527 leads)
- Email discovery via Hunter.io (22 emails found)
- Sync emails to Google Sheets (Column CB)
- Auto-sync after email discovery
- Manual sync button in web app
- API endpoint for programmatic sync

---

## Next Steps

1. **Discover more emails**: Use "🔍 Find All Emails" button
2. **Verify sync**: Check Google Sheet "Confirmed Best Email" column
3. **Monitor API usage**: Check `/api/email-usage-stats` endpoint
4. **Scale up**: Process remaining 505 leads without emails

---

## API Credits

- **Hunter.io**: 25 searches/month (free tier)
- **Current usage**: 22 emails discovered
- **Remaining**: ~3 searches

To scale up, consider upgrading Hunter.io plan or adding additional email APIs.

---

**Last Updated**: 2026-03-20
**Status**: ✅ Fully operational
