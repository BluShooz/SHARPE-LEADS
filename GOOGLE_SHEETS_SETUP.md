# Google Sheets Integration Setup Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies
```bash
cd /Users/jonsmith/leadforge-scraper
pip install gspread google-auth
```

### Step 2: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Sheets API**:
   - Search "Google Sheets API" in the search bar
   - Click "Enable"

### Step 3: Setup OAuth Credentials
✅ **Already done!** Your credentials file is already in place.

### Step 4: Authorize the App
1. Run the import script for the first time:
   ```bash
   python import_from_google_sheets.py
   ```
2. A browser window will open
3. Sign in to your Google account
4. Click **Allow** to give LeadForge access to your spreadsheets
5. The token will be saved automatically - you won't need to do this again!

### Step 5: Import Your Leads!

### Step 6: Import Your Leads!
```bash
cd /Users/jonsmith/leadforge-scraper
python import_from_google_sheets.py
```

---

## 📊 Your Current Google Sheet Data

Based on your sheet, you have:
- **527 total leads** (476 Strict Business + 51 Microbusiness)
- **527 unworked leads** (Call Status: NEW)
- **287 Priority A unworked leads**
- **0 overdue follow-ups**
- **0 do not call**

### Columns Available:
- Primary Link (website)
- Source Link (where lead came from)
- Phone
- Market (location)
- Presence Type (OWNED_WEBSITE, etc.)
- Caller Owner (UNASSIGNED, or names)
- Opportunity Stage (PROSPECT)
- Call Status (NEW, CONTACTED, etc.)
- Next Follow Up
- Next Best Action
- Weighted Opportunity Value
- Difficulty (EASY, MEDIUM, HARD)

---

## 🔄 What the Integration Does

### Import Features:
✅ Reads all 527 leads from your Google Sheet
✅ Maps sheet columns to LeadForge database structure
✅ Preserves existing data (Call Status, Owner, etc.)
✅ Skips duplicates based on website URL
✅ Shows progress for each imported lead

### Export Features:
✅ Pushes new scraped leads to your Google Sheet
✅ Updates lead status in the sheet
✅ Maintains your existing workflow
✅ Syncs both directions

---

## 🎯 Expected Results

After importing, you'll have:
1. **All 527 leads** in the LeadForge database
2. **LeadForge dashboard** populated with your existing leads
3. **Ability to scrape new leads** and add them to your sheet
4. **Sync functionality** to keep both systems updated

---

## 🛠️ Troubleshooting

### Error: "API not enabled"
- Go back to Step 2 and ensure Google Sheets API is enabled

### Error: "Insufficient permissions"
- Make sure you shared the sheet with the service account email (Step 5)

### Error: "credentials.json not found"
- Ensure the credentials file is in the project directory

### Error: "Spreadsheet not found"
- Check that the SHEET_ID in the script matches your sheet URL

---

## 📞 Need Help?

1. Check your credentials.json file format
2. Verify service account email has Editor access
3. Ensure Google Sheets API is enabled
4. Check the console for specific error messages

---

## 🚀 Next Steps

After successful import:
1. ✅ View your leads in the LeadForge dashboard
2. ✅ Use the scraper to find new leads
3. ✅ Export new leads back to your Google Sheet
4. ✅ Keep everything in sync!
