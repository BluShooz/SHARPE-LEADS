# SHARPE LEADS 🚀

AI-Powered Lead Generation System with Google Places API and Email Discovery

## 🎯 Overview

SHARPE LEADS is a complete lead generation and management system that uses Google Sheets as a master database ("poor man's database"). It integrates Google Places API for global business discovery and Hunter.io for email discovery, with a web interface for real-time lead management.

Generate leads from **any location worldwide** - San Francisco to Tokyo, London to Sydney. Simply provide GPS coordinates and let the system discover businesses in your target market.

## ✨ Features

- **Google Places API Integration**: Generate real business leads from Google Places
- **Email Discovery**: Automatic email discovery using Hunter.io API
- **Google Sheets Sync**: Bidirectional sync with Google Sheets as master database
- **Duplicate Prevention**: Automatic duplicate detection and prevention
- **Web Dashboard**: Real-time lead management interface
- **API Endpoints**: RESTful API for lead operations
- **Worldwide Coverage**: Generate leads from any location globally

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE SHEETS                             │
│            (Master Database - "Poor Man's DB")               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  "Imported Leads Clean" Worksheet                    │  │
│  │  - 846+ unique leads                                  │  │
│  │  - No duplicates                                      │  │
│  │  - Real-time sync                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
         ┌──────────────────┴──────────────────┐
         │                                      │
    ┌─────┴─────┐                         ┌─────┴─────┐
    │   READ    │                         │   WRITE   │
    └─────┬─────┘                         └─────┬─────┘
          │                                      │
          │                                      │
┌─────────┴───────────────┐          ┌─────────┴───────────────┐
│  Frontend Dashboard     │          │  Email Discovery        │
│                         │          │                         │
│  - Load leads           │          │  - Hunter.io API        │
│  - Display pipeline     │          │  - Direct to Sheets     │
│  - Sync button          │          │  - No local DB          │
└─────────────────────────┘          └─────────────────────────┘
          │
          │
┌─────────┴───────────────┐
│  Google Places API      │
│                         │
│  - Generate leads       │
│  - San Francisco, CA    │
│  - Add to Sheets        │
└─────────────────────────┘
```

## 🌐 Live Demo

**🚀 [Deployed on Vercel](https://sharpe-leads.vercel.app/)**

## 📋 Prerequisites

- Python 3.8+
- Google Cloud Account (for Service Account)
- Google Sheet
- Google Places API Key
- Hunter.io API Key (for email discovery)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jonathonsmith/SHARPE-LEADS.git
cd SHARPE-LEADS
```

### 2. Install Dependencies

```bash
pip3 install gspread google-auth requests flask
```

### 3. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create Service Account:
   - IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: "sharpe-leads-access"
5. Create and download JSON key
6. Save as `service_account.json` (NOT in git - add to .gitignore)

### 4. Google Sheets Setup

1. Create new Google Sheet
2. Note the SHEET_ID from URL
3. Share sheet with service account email
4. Create "Imported Leads Clean" worksheet
5. Add headers:

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Business Name | Phone | Website | Location | Industry | Rating | Reviews | Address | Email | Score |

### 5. Configure API Keys

Update the following files with your API keys:

- `google_sheets_integration.py`: SHEET_ID
- `sync_to_sheets.py`: SHEET_ID
- `email_to_sheets.py`: SHEET_ID, HUNTER_API_KEY
- `places_api_integration.py`: API_KEY (Google Places)

## 📖 Usage

### Generate Leads from Google Places API

```bash
python3 -c "
from places_api_integration import PlacesLeadGenerator
import json

generator = PlacesLeadGenerator()
leads = generator.search_businesses(
    query='Blue Bottle Coffee',
    location='37.7749,-122.4194',  # San Francisco
    max_results=1
)
print(json.dumps(leads[0], indent=2))
"
```

### Add Lead to Google Sheets

```bash
python3 -c "
import gspread
from google.oauth2.service_account import Credentials

scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('YOUR_SHEET_ID')
worksheet = sheet.worksheet('Imported Leads Clean')

lead_row = [
    'Business Name',
    'Phone Number',
    'https://website.com',
    'San Francisco, CA',
    'Industry',
    '4.5',
    '100',
    'Full Address',
    '',
    '95'
]

worksheet.append_row(lead_row)
print('✅ Lead added!')
"
```

### Discover Emails

```bash
python3 email_to_sheets.py 10
```

This will discover emails for 10 leads without emails.

### Start the API Server

```bash
python3 main.py
```

Server runs on: `http://localhost:8000`

## 🔑 API Endpoints

### Load Leads from Google Sheets
```
GET /api/leads/load-from-sheets
```

### Sync Emails to Google Sheets
```
POST /api/sync-to-sheets
Content-Type: application/json

{
  "limit": 10
}
```

## 📁 Project Structure

```
SHARPE-LEADS/
├── google_sheets_integration.py    # Google Sheets client
├── sync_to_sheets.py               # Sync emails to Sheets
├── email_to_sheets.py              # Email discovery
├── places_api_integration.py       # Google Places API
├── main.py                         # API server
├── service_account.json            # Google credentials (NOT in git)
├── .gitignore                      # Excluded files
└── README.md                       # This file
```

## 🎯 Key Features Explained

### Google Sheets as Master Database
- No local database needed
- All data flows directly to/from Google Sheets
- "Poor man's database" approach
- Real-time collaboration

### Duplicate Prevention
- Automatic detection before adding leads
- Checks by business name
- Skips duplicates with alert

### Global Lead Generation
- Supports any location worldwide using GPS coordinates
- Pre-configured with major city examples
- Flexible location formatting (City, State, Country)
- Industry-specific search capabilities

### Email Discovery
- Hunter.io integration
- Direct write to Google Sheets
- Confidence scoring
- No intermediate storage

## 🐛 Troubleshooting

### Issue: "Connection failed"
- Verify `service_account.json` exists
- Check Google Sheet is shared with service account email
- Confirm SHEET_ID is correct

### Issue: "Email column not found"
- Verify worksheet name is "Imported Leads Clean"
- Check headers match exactly

### Issue: "Protected cell" error
- Use "Imported Leads Clean" worksheet
- Don't use protected worksheets

## 📊 Current Statistics

- **Total Leads**: 846+
- **Unique Leads**: 846 (no duplicates)
- **Emails Discovered**: Ongoing
- **Location**: San Francisco, CA

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🔗 Links

- **Live Demo**: [https://sharpe-leads.vercel.app](https://sharpe-leads.vercel.app)
- **GitHub Repository**: [https://github.com/jonathonsmith/SHARPE-LEADS](https://github.com/jonathonsmith/SHARPE-LEADS)
- **Issues**: [https://github.com/jonathonsmith/SHARPE-LEADS/issues](https://github.com/jonathonsmith/SHARPE-LEADS/issues)

## 👨‍💻 Author

Built with ❤️ by SHARPE

---

**Note**: This system uses Google Sheets as the primary database. Ensure your Google Sheet is properly shared with the service account email for full functionality.
