#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     LEADFORGE AI - SYNC WORKFLOW TEST                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Step 1: Check database status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 leads.db 'SELECT COUNT(*) as total_leads FROM leads;'
sqlite3 leads.db 'SELECT COUNT(*) as leads_with_emails FROM leads WHERE email IS NOT NULL AND email != "";'
echo ""

echo "🔄 Step 2: Test sync endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/sync-to-sheets \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
echo ""

echo "✅ Step 3: Verify server is running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s http://localhost:8000/api/test | python3 -m json.tool
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   TEST COMPLETE                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 To test in the web app:"
echo "   1. Open: file:///Users/jonsmith/Desktop/leadforge-demo.html"
echo "   2. Click '🔍 Find All Emails' → Wait 3 seconds for auto-sync"
echo "   3. Or click '🔄 Sync to Sheets' for manual sync"
echo ""
