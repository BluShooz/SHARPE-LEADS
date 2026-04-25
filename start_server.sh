#!/bin/bash

# LeadForge AI Backend Server Startup Script
# Starts the server with Phase 1 features enabled

echo "=========================================="
echo "🚀 Starting LeadForge AI Backend Server"
echo "=========================================="
echo ""

cd /Users/jonsmith/leadforge-scraper

echo "📁 Working directory: $(pwd)"
echo ""
echo "🛡️  Phase 1 Features:"
echo "  ✅ Data Validation"
echo "  ✅ Error Handling & Retry Logic"
echo "  ✅ Health Monitoring"
echo "  ✅ Enhanced Logging"
echo ""
echo "📝 Log file: leadforge.log"
echo "🏥 Health check: http://localhost:8000/api/health"
echo ""
echo "=========================================="
echo "Server starting on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

python3 main.py
