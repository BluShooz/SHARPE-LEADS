"""
SHARPE LEADS - API Handler for Vercel
Serverless function for lead generation and management
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
try:
    from google_sheets_integration import GoogleSheetsClient
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

try:
    from places_api_integration import PlacesLeadGenerator
    PLACES_AVAILABLE = True
except ImportError:
    PLACES_AVAILABLE = False

try:
    from sync_to_sheets import sync_emails
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False


class handler(BaseHTTPRequestHandler):
    """HTTP request handler for Vercel serverless function"""

    def do_GET(self):
        """Handle GET requests"""
        path = self.path.rstrip('/')

        # Root path - API info
        if path == '/' or path == '':
            self._send_json({
                "name": "SHARPE LEADS API",
                "version": "1.0.0",
                "status": "active",
                "endpoints": {
                    "GET /api/health": "Health check",
                    "GET /api/leads/load-from-sheets": "Load leads from Google Sheets",
                    "POST /api/generate-lead": "Generate lead from Places API",
                    "POST /api/sync-to-sheets": "Sync emails to Google Sheets"
                },
                "integrations": {
                    "google_sheets": SHEETS_AVAILABLE,
                    "places_api": PLACES_AVAILABLE,
                    "sync": SYNC_AVAILABLE
                }
            })
            return

        # Health check
        if path == '/api/health':
            self._send_json({
                "status": "healthy",
                "timestamp": self._get_timestamp(),
                "integrations": {
                    "google_sheets": SHEETS_AVAILABLE,
                    "places_api": PLACES_AVAILABLE,
                    "sync": SYNC_AVAILABLE
                }
            })
            return

        # Load leads from Google Sheets
        if path == '/api/leads/load-from-sheets':
            if not SHEETS_AVAILABLE:
                self._send_error(503, "Google Sheets integration not available")
                return

            try:
                client = GoogleSheetsClient()
                leads = client.read_all_leads()
                self._send_json({
                    "success": True,
                    "count": len(leads),
                    "leads": leads[:100],  # Limit to 100 for performance
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error loading leads: {str(e)}")
            return

        # Unknown path
        self._send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests"""
        path = self.path.rstrip('/')

        # Generate lead from Places API
        if path == '/api/generate-lead':
            if not PLACES_AVAILABLE:
                self._send_error(503, "Google Places API not available")
                return

            try:
                # Read POST data
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    data = {}

                query = data.get('query', 'coffee shop')
                location = data.get('location', '37.7749,-122.4194')  # San Francisco
                max_results = data.get('max_results', 1)

                generator = PlacesLeadGenerator()
                leads = generator.search_businesses(
                    query=query,
                    location=location,
                    max_results=max_results
                )

                self._send_json({
                    "success": True,
                    "count": len(leads),
                    "leads": leads,
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error generating lead: {str(e)}")
            return

        # Sync emails to Google Sheets
        if path == '/api/sync-to-sheets':
            if not SYNC_AVAILABLE:
                self._send_error(503, "Sync functionality not available")
                return

            try:
                # Read POST data
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    data = {}

                limit = data.get('limit', None)

                result = sync_emails(limit=limit)
                self._send_json(result)
            except Exception as e:
                self._send_error(500, f"Error syncing to sheets: {str(e)}")
            return

        # Unknown path
        self._send_error(404, "Endpoint not found")

    def _send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": False,
            "error": message
        }).encode())

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# For local testing
if __name__ == '__main__':
    from http.server import HTTPServer

    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('localhost', port), handler)
    print(f"Server running on port {port}")
    server.serve_forever()
