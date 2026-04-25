# Service Account Setup Guide (Simple & Reliable)

## 🚀 5-Minute Setup

### Step 1: Create Service Account
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Make sure your project "project-996219d7-7e6b-4702-b17" is selected
3. Click **+ CREATE SERVICE ACCOUNT**
4. **Service account name**: `leadforge-scraper`
5. Click **CREATE AND CONTINUE**
6. Skip granting roles (click **DONE**)

### Step 2: Create Service Account Key
1. Click on the service account you just created
2. Go to **KEYS** tab
3. Click **ADD KEY** → **Create New Key**
4. Select **JSON** (important!)
5. Click **CREATE**
6. A JSON file will download (name will be like `project-xxxxx-xxxxx.json`)

### Step 3: Save Service Account Key
```bash
# Move the downloaded file to the project directory
mv ~/Downloads/project-*.json /Users/jonsmith/leadforge-scraper/service_account.json
```

### Step 4: Share Your Google Sheet
1. Open the `service_account.json` file
2. Copy the `client_email` value (looks like: `leadforge-scraper@project-xxx.iam.gserviceaccount.com`)
3. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo/edit
4. Click **Share** button
5. Paste the service account email
6. Give it **Editor** access
7. Click **Send**

### Step 5: Import Your Leads!
```bash
cd /Users/jonsmith/leadforge-scraper
python3 import_auto.py
```

---

## ✅ What's Different About Service Accounts?

**Service Accounts:**
- ✅ No OAuth verification needed
- ✅ No test users needed
- ✅ No browser popup
- ✅ Works immediately
- ✅ More reliable for server scripts

**OAuth (what we tried before):**
- ❌ Requires verification
- ❌ Requires test users
- ❌ Browser popup
- ❌ More complex

---

## 🎯 Done!

Once you complete these 5 steps, your 527 leads will import automatically!

Let me know when you've created the service account and I'll help you with the rest!
