"""
SHARPE LEADS - Complete API Handler for Vercel
Serverless function for lead generation and management
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import re

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

# Import email enrichment if available
try:
    from email_enrichment import EmailEnrichmentService
    import dotenv
    dotenv.load_dotenv()
    HUNTER_API_KEY = os.getenv('HUNTER_IO_API_KEY')
    if HUNTER_API_KEY:
        email_service = EmailEnrichmentService(hunter_api_key=HUNTER_API_KEY)
        EMAIL_AVAILABLE = True
    else:
        EMAIL_AVAILABLE = False
except ImportError:
    EMAIL_AVAILABLE = False


class handler(BaseHTTPRequestHandler):
    """HTTP request handler for Vercel serverless function"""

    def do_GET(self):
        """Handle GET requests"""
        path = self.path.rstrip('/')
        # Remove query parameters from path for routing
        if '?' in path:
            path = path.split('?')[0]
        parts = path.split('/')

        # Root path - API info
        if path == '/' or path == '':
            self._send_json({
                "name": "SHARPE LEADS API",
                "version": "1.0.0",
                "status": "active",
                "endpoints": {
                    "GET /": "API information",
                    "GET /api/health": "Health check",
                    "GET /api/leads/load-from-sheets": "Load leads from Google Sheets",
                    "GET /api/sheets-leads": "Load leads from sheets (alternative)",
                    "GET /api/leads": "Get all leads",
                    "GET /api/places-search": "Search Google Places",
                    "POST /api/scrape": "Generate leads from Google Places",
                    "POST /api/generate-lead": "Generate single lead from Places API",
                    "POST /api/sync-to-sheets": "Sync emails to Google Sheets",
                    "POST /api/leads/{id}/find-email": "Find email for lead",
                    "POST /api/leads/{id}/validate-email": "Validate email for lead",
                    "POST /api/leads/batch/find-email": "Batch find emails",
                    "POST /api/leads/batch/validate-email": "Batch validate emails",
                    "DELETE /api/leads/{id}": "Delete lead"
                },
                "integrations": {
                    "google_sheets": SHEETS_AVAILABLE,
                    "places_api": PLACES_AVAILABLE,
                    "email_discovery": EMAIL_AVAILABLE,
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
                    "email_discovery": EMAIL_AVAILABLE,
                    "sync": SYNC_AVAILABLE
                }
            })
            return

        # Load leads from Google Sheets (original endpoint)
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

        # Alternative sheets leads endpoint
        if path == '/api/sheets-leads':
            if not SHEETS_AVAILABLE:
                self._send_error(503, "Google Sheets integration not available")
                return

            try:
                client = GoogleSheetsClient()
                leads = client.read_all_leads()
                self._send_json({
                    "success": True,
                    "leads": leads,
                    "count": len(leads),
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error loading leads: {str(e)}")
            return

        # Get all leads
        if path == '/api/leads':
            if not SHEETS_AVAILABLE:
                self._send_error(503, "Google Sheets integration not available")
                return

            try:
                # Parse query parameters
                query_params = {}
                if '?' in self.path:
                    query_string = self.path.split('?')[1]
                    for param in query_string.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = value

                limit = int(query_params.get('limit', 100))

                client = GoogleSheetsClient()
                all_leads = client.read_all_leads()

                # Apply limit
                leads = all_leads[:limit] if limit else all_leads

                self._send_json({
                    "success": True,
                    "leads": leads,
                    "count": len(leads),
                    "total": len(all_leads),
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error loading leads: {str(e)}")
            return

        # Google Places search
        if path == '/api/places-search':
            if not PLACES_AVAILABLE:
                self._send_error(503, "Google Places API not available")
                return

            try:
                query_params = {}
                if '?' in self.path:
                    query_string = self.path.split('?')[1]
                    for param in query_string.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = value

                query = query_params.get('query', 'coffee shop')
                location = query_params.get('location', '37.7749,-122.4194')
                max_results = int(query_params.get('max_results', 10))

                generator = PlacesLeadGenerator()
                leads = generator.search_businesses(
                    query=query,
                    location=location,
                    max_results=max_results
                )

                self._send_json({
                    "success": True,
                    "leads": leads,
                    "count": len(leads),
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error searching places: {str(e)}")
            return

        # Lead-specific operations (find-email, validate-email)
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads':
            lead_id = parts[3]
            action = parts[4] if len(parts) >= 5 else None

            if action == 'find-email':
                if not EMAIL_AVAILABLE:
                    self._send_error(503, "Email discovery not available")
                    return

                try:
                    if email_service:
                        # Get lead details from sheets
                        client = GoogleSheetsClient()
                        all_leads = client.read_all_leads()

                        # Find the lead
                        lead = None
                        for l in all_leads:
                            if str(l.get('id', '')) == lead_id or l.get('business_name', '') == lead_id:
                                lead = l
                                break

                        if not lead or not lead.get('website'):
                            self._send_error(404, "Lead not found or no website")
                            return

                        # Extract domain and discover email
                        website = lead['website']
                        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

                        result = email_service.discover_email(domain, lead.get('business_name', ''))

                        if result.get('success'):
                            # Update the lead in Google Sheets
                            client.add_lead_to_sheet({
                                'business_name': lead['business_name'],
                                'email': result['email'],
                                'website': lead['website'],
                                'phone': lead.get('phone', ''),
                                'location': lead.get('location', ''),
                                'industry': lead.get('industry', ''),
                                'score': lead.get('score', 70),
                                'rating': lead.get('rating'),
                                'reviews_count': lead.get('reviews_count', 0),
                                'address': lead.get('address', '')
                            })

                        self._send_json(result)
                    else:
                        self._send_error(503, "Email service not available")
                except Exception as e:
                    self._send_error(500, f"Error finding email: {str(e)}")
                return

            if action == 'validate-email':
                if not EMAIL_AVAILABLE:
                    self._send_error(503, "Email validation not available")
                    return

                try:
                    if email_service:
                        # Get lead details from sheets
                        client = GoogleSheetsClient()
                        all_leads = client.read_all_leads()

                        # Find the lead
                        lead = None
                        for l in all_leads:
                            if str(l.get('id', '')) == lead_id or l.get('business_name', '') == lead_id:
                                lead = l
                                break

                        if not lead or not lead.get('email'):
                            self._send_error(404, "Lead not found or no email")
                            return

                        # Validate email
                        result = email_service.validate_email(lead['email'])
                        self._send_json(result)
                    else:
                        self._send_error(503, "Email service not available")
                except Exception as e:
                    self._send_error(500, f"Error validating email: {str(e)}")
                return

        # Get specific lead
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads' and parts[3] != 'batch':
            lead_id = parts[3]

            if not SHEETS_AVAILABLE:
                self._send_error(503, "Google Sheets integration not available")
                return

            try:
                client = GoogleSheetsClient()
                all_leads = client.read_all_leads()

                # Find the lead
                lead = None
                for l in all_leads:
                    if str(l.get('id', '')) == lead_id or l.get('business_name', '') == lead_id:
                        lead = l
                        break

                if not lead:
                    self._send_error(404, "Lead not found")
                else:
                    self._send_json({
                        "success": True,
                        "lead": lead,
                        "timestamp": self._get_timestamp()
                    })
            except Exception as e:
                self._send_error(500, f"Error loading lead: {str(e)}")
            return

        # Unknown path
        self._send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests"""
        path = self.path.rstrip('/')
        # Remove query parameters from path for routing
        if '?' in path:
            path = path.split('?')[0]
        parts = path.split('/')

        # Scrape endpoint - main lead generation
        if path == '/api/scrape':
            if not PLACES_AVAILABLE:
                self._send_error(503, "Google Places API not available")
                return

            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                industry = data.get('industry', 'Software Company')
                location = data.get('location', 'San Francisco, CA')
                max_leads = int(data.get('max_leads', 20))
                min_score = int(data.get('min_score', 60))

                # Convert location to coordinates
                location_coords = self._location_to_coords(location)

                generator = PlacesLeadGenerator()
                leads = generator.search_businesses(
                    query=industry,
                    location=location_coords,
                    max_results=max_leads
                )

                # Filter by score
                filtered_leads = [lead for lead in leads if lead.get('score', 0) >= min_score]

                self._send_json({
                    "success": True,
                    "leads": filtered_leads,
                    "count": len(filtered_leads),
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error scraping: {str(e)}")
            return

        # Generate lead from Places API (single)
        if path == '/api/generate-lead':
            if not PLACES_AVAILABLE:
                self._send_error(503, "Google Places API not available")
                return

            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                query = data.get('query', 'coffee shop')
                location = data.get('location', '37.7749,-122.4194')
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
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                limit = data.get('limit', None)

                result = sync_emails(limit=limit)
                self._send_json(result)
            except Exception as e:
                self._send_error(500, f"Error syncing to sheets: {str(e)}")
            return

        # Batch email operations
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads' and parts[3] == 'batch':
            action = parts[4] if len(parts) >= 5 else None

            if action == 'find-email':
                if not EMAIL_AVAILABLE:
                    self._send_error(503, "Email discovery not available")
                    return

                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    lead_ids = data.get('lead_ids', [])

                    results = []
                    for lead_id in lead_ids:
                        # Find lead and discover email
                        client = GoogleSheetsClient()
                        all_leads = client.read_all_leads()

                        lead = None
                        for l in all_leads:
                            if str(l.get('id', '')) == lead_id or l.get('business_name', '') == lead_id:
                                lead = l
                                break

                        if lead and lead.get('website'):
                            domain = lead['website'].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                            result = email_service.discover_email(domain, lead.get('business_name', ''))

                            if result.get('success'):
                                # Update in sheets
                                client.add_lead_to_sheet({
                                    'business_name': lead['business_name'],
                                    'email': result['email'],
                                    'website': lead['website'],
                                    'phone': lead.get('phone', ''),
                                    'location': lead.get('location', ''),
                                    'industry': lead.get('industry', ''),
                                    'score': lead.get('score', 70)
                                })

                            results.append({
                                'lead_id': lead_id,
                                'business_name': lead.get('business_name'),
                                'result': result
                            })

                    self._send_json({
                        "success": True,
                        "processed": len(results),
                        "results": results,
                        "timestamp": self._get_timestamp()
                    })
                except Exception as e:
                    self._send_error(500, f"Error in batch operation: {str(e)}")
                return

            if action == 'validate-email':
                if not EMAIL_AVAILABLE:
                    self._send_error(503, "Email validation not available")
                    return

                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    emails = data.get('emails', [])

                    results = []
                    for email in emails:
                        result = email_service.validate_email(email)
                        results.append({
                            'email': email,
                            'result': result
                        })

                    self._send_json({
                        "success": True,
                        "processed": len(results),
                        "results": results,
                        "timestamp": self._get_timestamp()
                    })
                except Exception as e:
                    self._send_error(500, f"Error in batch operation: {str(e)}")
                return

        # Unknown path
        self._send_error(404, "Endpoint not found")

    def do_DELETE(self):
        """Handle DELETE requests"""
        path = self.path.rstrip('/')
        # Remove query parameters from path for routing
        if '?' in path:
            path = path.split('?')[0]
        parts = path.split('/')

        # Delete specific lead
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads':
            lead_id = parts[3]

            if not SHEETS_AVAILABLE:
                self._send_error(503, "Google Sheets integration not available")
                return

            try:
                # For now, we'll just return success
                # In a real implementation, you'd need to delete from Google Sheets
                self._send_json({
                    "success": True,
                    "message": f"Lead {lead_id} marked for deletion",
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                self._send_error(500, f"Error deleting lead: {str(e)}")
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

    def _location_to_coords(self, location):
        """Convert city name to coordinates"""
        # Major city coordinates
        coords = {
            'San Francisco, CA': '37.7749,-122.4194',
            'New York, NY': '40.7128,-74.0060',
            'Austin, TX': '30.2672,-97.7431',
            'Seattle, WA': '47.6062,-122.3321',
            'Denver, CO': '39.73922,-104.9903',
            'Miami, FL': '25.7617,-80.1918',
            'Chicago, IL': '41.8781,-87.6298',
            'Boston, MA': '42.3601,-71.0589',
            'Los Angeles, CA': '34.0522,-118.2437',
            'Phoenix, AZ': '33.4484,-112.0740',
            'Dallas, TX': '32.7767,-96.7970',
            'Atlanta, GA': '33.7490,-84.3880'
        }

        return coords.get(location, '37.7749,-122.4194')  # Default to SF


# For local testing
if __name__ == '__main__':
    from http.server import HTTPServer

    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('localhost', port), handler)
    print(f"Server running on port {port}")
    server.serve_forever()
