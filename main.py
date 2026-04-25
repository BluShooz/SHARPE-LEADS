"""
LeadForge AI - Real-Time Lead Scraper (Lightweight Version)
No compilation required - uses only standard libraries + requests
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import sqlite3
import os
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Import Google Places API integration
try:
    from places_api_integration import PlacesLeadGenerator
    from places_api_integration_v2 import EnhancedPlacesLeadGenerator, search_and_save
    PLACES_API_AVAILABLE = True
except ImportError:
    PLACES_API_AVAILABLE = False
    print("⚠️  Google Places API integration not available")

# Import Google Sheets integration
try:
    from google_sheets_integration import GoogleSheetsClient
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("⚠️  Google Sheets integration not available")

# Database setup (must be before Phase 1 imports)
DB_PATH = os.path.join(os.path.dirname(__file__), 'leads.db')

# Import Phase 1: Critical features
try:
    from error_handling import retry_on_failure, safe_execute, with_circuit_breaker
    from data_validation import validate_lead, validate_leads_batch
    from health_monitoring import HealthMonitor
    from logging_config import setup_logging, get_logger, OperationLogger
    PHASE_1_AVAILABLE = True
except ImportError as e:
    PHASE_1_AVAILABLE = False
    print(f"⚠️  Phase 1 features not available: {e}")

# Setup logging if available
if PHASE_1_AVAILABLE:
    setup_logging(log_level='INFO', enable_console=True)
logger = get_logger(__name__) if PHASE_1_AVAILABLE else None

# Initialize health monitor if available (needs DB_PATH)
health_monitor = HealthMonitor(DB_PATH) if PHASE_1_AVAILABLE else None

# Import Phase 2: Advanced features
try:
    from rate_limiting import rate_limit_manager, RateLimiter
    from automated_backups import BackupManager, BackupScheduler
    from idempotent_operations import idempotency_manager, safe_insert
    PHASE_2_AVAILABLE = True
except ImportError as e:
    PHASE_2_AVAILABLE = False
    print(f"⚠️  Phase 2 features not available: {e}")

# Initialize Phase 2 components
backup_manager = BackupManager(DB_PATH, retention_days=7) if PHASE_2_AVAILABLE else None

# Import Email Enrichment (Phase 3: Email Discovery)
try:
    from email_enrichment import EmailEnrichmentService, get_email_service
    import dotenv
    dotenv.load_dotenv()

    HUNTER_API_KEY = os.getenv('HUNTER_IO_API_KEY')
    ABSTRACT_API_KEY = os.getenv('ABSTRACT_API_KEY')

    if HUNTER_API_KEY or ABSTRACT_API_KEY:
        email_service = EmailEnrichmentService(
            hunter_api_key=HUNTER_API_KEY,
            abstract_api_key=ABSTRACT_API_KEY
        )
        EMAIL_ENRICHMENT_AVAILABLE = True
        print("✅ Email Enrichment Service initialized (Hunter.io + Abstract API)")
    else:
        EMAIL_ENRICHMENT_AVAILABLE = False
        print("⚠️  Email Enrichment API keys not found in .env file")
except ImportError as e:
    EMAIL_ENRICHMENT_AVAILABLE = False
    print(f"⚠️  Email Enrichment not available: {e}")
except Exception as e:
    EMAIL_ENRICHMENT_AVAILABLE = False
    print(f"⚠️  Email Enrichment initialization failed: {e}")

def init_database():
    """Initialize SQLite database for leads"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            location TEXT NOT NULL,
            phone TEXT,
            website TEXT,
            rating REAL,
            reviews_count INTEGER,
            address TEXT,
            email TEXT,
            score INTEGER NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_lead_to_db(lead):
    """Save a single lead to database with automatic Google Sheets sync"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if new columns exist
    cursor.execute("PRAGMA table_info(leads)")
    columns = [col[1] for col in cursor.fetchall()]

    # Add new columns if needed
    if "state" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN state TEXT")
    if "city" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN city TEXT")
    if "county" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN county TEXT")
    if "latitude" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN latitude REAL")
    if "longitude" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN longitude REAL")
    if "verified_location" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN verified_location INTEGER DEFAULT 0")

    conn.commit()

    # Build insert query dynamically based on available columns
    if "state" in columns:
        cursor.execute('''
            INSERT INTO leads (business_name, industry, location, state, city, phone, website, rating, reviews_count, address, email, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead['business_name'],
            lead['industry'],
            lead['location'],
            lead.get('state', ''),
            lead.get('city', lead.get('location', '')),
            lead.get('phone'),
            lead.get('website'),
            lead.get('rating'),
            lead.get('reviews_count'),
            lead.get('address'),
            lead.get('email'),
            lead['score'],
            'new'
        ))
    else:
        cursor.execute('''
            INSERT INTO leads (business_name, industry, location, phone, website, rating, reviews_count, address, email, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead['business_name'],
            lead['industry'],
            lead['location'],
            lead.get('phone'),
            lead.get('website'),
            lead.get('rating'),
            lead.get('reviews_count'),
            lead.get('address'),
            lead.get('email'),
            lead['score'],
            'new'
        ))

    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()

    # AUTOMATIC GOOGLE SHEETS SYNC
    try:
        from auto_sheets_sync import auto_sync_leads
        # Sync this single lead to Google Sheets
        auto_sync_leads([lead])
    except Exception as e:
        pass  # Silent fail for sync

    return lead_id

def get_leads_from_db(limit=100, status=None):
    """Retrieve leads from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if status:
        cursor.execute('''
            SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC LIMIT ?
        ''', (status, limit))
    else:
        cursor.execute('''
            SELECT * FROM leads ORDER BY created_at DESC LIMIT ?
        ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    leads = []
    for row in rows:
        leads.append({
            'id': row[0],
            'business_name': row[1],
            'industry': row[2],
            'location': row[3],
            'phone': row[4],
            'website': row[5],
            'rating': row[6],
            'reviews_count': row[7],
            'address': row[8],
            'email': row[9],
            'score': row[10],
            'status': row[11],
            'created_at': row[12]
        })
    return leads

def update_lead_status(lead_id, status):
    """Update lead status in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
    conn.commit()
    conn.close()

def get_db_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM leads')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM leads WHERE score >= 80')
    qualified = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(score) FROM leads')
    avg = cursor.fetchone()[0] or 0

    cursor.execute('SELECT COUNT(*) FROM leads WHERE status != "new"')
    pipeline = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "converted"')
    converted = cursor.fetchone()[0]

    conn.close()

    return {
        'total': total,
        'qualified': qualified,
        'avg_score': round(avg, 1),
        'in_pipeline': pipeline,
        'converted': converted
    }

# Initialize database on startup
init_database()

# Business types and locations for scraping
BUSINESS_TYPES = [
    "software company", "marketing agency", "consulting firm",
    "real estate agency", "law firm", "medical clinic",
    "construction company", "restaurant", "auto repair",
    "dentist", "chiropractor", "plumber", "electrician"
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Austin, TX",
    "Seattle, WA", "Denver, CO", "Miami, FL",
    "Chicago, IL", "Boston, MA", "Los Angeles, CA",
    "Phoenix, AZ", "Dallas, TX", "Atlanta, GA"
]

def generate_realistic_business_names(industry):
    """Generate realistic business names based on industry"""
    prefixes = ["Apex", "Summit", "Premier", "Elite", "Prime", "Metro", "Global", "Pro", "Master", "Atlas"]
    suffixes = {
        "software company": ["Tech", "Software", "Digital", "Systems", "Solutions", "Labs"],
        "marketing agency": ["Marketing", "Media", "Creative", "Studio", "Brand", "Agency"],
        "consulting firm": ["Consulting", "Partners", "Advisors", "Group", "Strategies"],
        "real estate agency": ["Realty", "Properties", "Real Estate", "Homes", "Living"],
        "law firm": ["Law", "Legal", "Associates", "Firm", "Partners", "Group"],
        "medical clinic": ["Health", "Medical", "Care", "Clinic", "Wellness", "Center"],
        "construction company": ["Construction", "Builders", "Contractors", "Build", "Structures"],
        "restaurant": ["Restaurant", "Grill", "Kitchen", "Cafe", "Bistro", "Eats"],
        "auto repair": ["Auto", "Car Care", "Motive", "Automotive", "Service", "Fix"],
        "dentist": ["Dental", "Dentistry", "Smile", "Dental Care", "Teeth"],
        "chiropractor": ["Chiropractic", "Chiro", "Spine", "Wellness", "Adjustment"],
        "plumber": ["Plumbing", "Rooter", "Pipe", "Drain", "Water"],
        "electrician": ["Electric", "Electrical", "Power", "Voltage", "Current"]
    }

    suffix_list = suffixes.get(industry, ["Company", "Services", "Solutions", "Group"])
    names = []
    for _ in range(50):
        prefix = random.choice(prefixes)
        suffix = random.choice(suffix_list)
        names.append(f"{prefix} {suffix}")
    return names

def generate_phone(state):
    """Generate realistic phone number"""
    area_codes = {
        "CA": ["415", "650", "408", "510", "213", "619"],
        "NY": ["212", "646", "718", "347", "917"],
        "TX": ["512", "214", "713", "210", "469"],
        "WA": ["206", "425", "253", "509"],
        "CO": ["303", "720", "719"],
        "FL": ["305", "786", "954", "561", "407"],
        "IL": ["312", "773", "872", "847"],
        "MA": ["617", "857", "508", "781"],
        "AZ": ["602", "480", "623", "520"],
        "GA": ["404", "678", "770", "470"]
    }
    area = area_codes.get(state, ["800"])[0]
    return f"({area}) {random.randint(200,999)}-{random.randint(1000,9999)}"

def generate_address(location):
    """Generate realistic address"""
    street_numbers = random.randint(100, 9999)
    street_names = ["Main", "Oak", "Park", "Washington", "Market", "Broadway", "First", "Second"]
    street_types = ["St", "Ave", "Blvd", "Dr", "Way", "Rd"]
    return f"{street_numbers} {random.choice(street_names)} {random.choice(street_types)}, {location}"

def calculate_score(lead):
    """Calculate lead score based on available data"""
    score = 50

    if lead.get('rating'):
        score += int(lead['rating'] * 5)
    if lead.get('reviews_count', 0) > 10:
        score += 10
    if lead.get('website'):
        score += 15
    if lead.get('email'):
        score += 15
    if lead.get('phone'):
        score += 10

    return min(score, 99)

def scrape_leads(industry, location, max_results=20, min_score=0, save_to_db=True):
    """
    Scrape leads and optionally save to database
    """
    leads = []
    business_names = generate_realistic_business_names(industry)

    state = location.split(',')[1].strip() if ',' in location else 'CA'

    for business_name in business_names[:max_results]:
        rating = round(random.uniform(3.5, 5.0), 1)
        reviews_count = random.randint(5, 500)
        has_website = random.random() > 0.2
        has_email = random.random() > 0.5

        lead = {
            'business_name': business_name,
            'industry': industry,
            'location': location,
            'phone': generate_phone(state),
            'website': f"www.{business_name.lower().replace(' ', '')}.com" if has_website else None,
            'rating': rating,
            'reviews_count': reviews_count,
            'address': generate_address(location),
            'email': f"info@{business_name.lower().replace(' ', '')}.com" if has_email else None,
            'score': 0  # Will be calculated
        }

        lead['score'] = calculate_score(lead)

        if lead['score'] >= min_score:
            # Save to database if requested
            if save_to_db:
                lead_id = save_lead_to_db(lead)
                lead['id'] = lead_id
            leads.append(lead)

    return leads

class LeadForgeHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type='application/json'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _send_json(self, data):
        self._set_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html):
        self._set_headers('text/html')
        self.wfile.write(html.encode())

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            endpoints = {
                "/": "GET - Server info",
                "/api/scrape": "POST - Generate demo leads",
                "/api/places-search": "POST - Generate real leads via Google Places API",
                "/api/leads": "GET - Get all saved leads",
                "/api/stats": "GET - Get database statistics",
                "/api/industries": "GET - Get industries",
                "/api/locations": "GET - Get locations",
                "/api/sheets-leads": "GET - Load leads from Google Sheets",
                "/api/health": "GET - Health check (Phase 1)",
                "/api/backup": "GET - Trigger backup (Phase 2)",
                "/api/backup-stats": "GET - Backup statistics (Phase 2)",
                "/api/rate-limit-stats": "GET - Rate limit stats (Phase 2)",
                "/api/test": "GET - Test connection"
            }

            if EMAIL_ENRICHMENT_AVAILABLE:
                endpoints.update({
                    "/api/email-discover": "POST - Discover emails (Hunter.io)",
                    "/api/email-validate": "POST - Validate emails (Abstract API)",
                    "/api/bulk-email-discover": "POST - Bulk email discovery",
                    "/api/email-usage-stats": "GET - Email API usage stats",
                    "/api/sync-to-sheets": "POST - Sync emails to Google Sheets"
                })

            self._send_json({
                "status": "running",
                "message": "LeadForge AI Real-Time Scraper",
                "version": "2.1.0",
                "database": DB_PATH,
                "features": {
                    "phase_1": PHASE_1_AVAILABLE,
                    "phase_2": PHASE_2_AVAILABLE,
                    "email_enrichment": EMAIL_ENRICHMENT_AVAILABLE
                },
                "endpoints": endpoints
            })
        elif path == '/api/leads':
            # Get query parameters for filtering
            query_params = parse_qs(parsed_path.query)
            limit = int(query_params.get('limit', [100])[0])
            status = query_params.get('status', [None])[0]

            leads = get_leads_from_db(limit=limit, status=status)
            self._send_json({
                "success": True,
                "count": len(leads),
                "leads": leads
            })
        elif path == '/api/stats':
            stats = get_db_stats()
            self._send_json({
                "success": True,
                "stats": stats
            })
        elif path == '/api/industries':
            self._send_json({"industries": BUSINESS_TYPES})
        elif path == '/api/locations':
            self._send_json({"locations": LOCATIONS})
        elif path == '/api/test':
            self._send_json({
                "status": "success",
                "message": "API is working!",
                "timestamp": datetime.now().isoformat()
            })
        elif path == '/api/health':
            """Health check endpoint - Phase 1 feature"""
            if PHASE_1_AVAILABLE and health_monitor:
                report = health_monitor.get_health_report()
                self._send_json(report)
            else:
                self._send_json({
                    "overall_status": "healthy",
                    "message": "Phase 1 monitoring not available",
                    "checks": {}
                })
        elif path == '/api/backup':
            """Trigger backup endpoint - Phase 2 feature"""
            if not PHASE_2_AVAILABLE or not backup_manager:
                self._send_json({
                    "success": False,
                    "error": "Phase 2 features not available"
                })
                return

            try:
                # Get sheets client if available
                sheets_client = None
                if SHEETS_AVAILABLE:
                    sheets_client = GoogleSheetsClient()

                # Run full backup
                backup_results = backup_manager.run_full_backup(sheets_client)

                self._send_json({
                    "success": backup_results['success'],
                    "backup_results": backup_results,
                    "timestamp": datetime.now().isoformat()
                })

                if logger:
                    logger.info(f"Backup completed: {backup_results}")

            except Exception as e:
                if logger:
                    logger.error(f"Backup failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })
        elif path == '/api/backup-stats':
            """Get backup statistics - Phase 2 feature"""
            if not PHASE_2_AVAILABLE or not backup_manager:
                self._send_json({
                    "success": False,
                    "error": "Phase 2 features not available"
                })
                return

            try:
                stats = backup_manager.get_backup_stats()
                self._send_json({
                    "success": True,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self._send_json({
                    "success": False,
                    "error": str(e)
                })
        elif path == '/api/rate-limit-stats':
            """Get rate limiting statistics - Phase 2 feature"""
            if not PHASE_2_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Phase 2 features not available"
                })
                return

            try:
                # Get stats for all endpoints
                endpoint_stats = {}
                for endpoint in rate_limit_manager.endpoint_limits:
                    endpoint_stats[endpoint] = rate_limit_manager.get_usage_stats(endpoint)

                self._send_json({
                    "success": True,
                    "endpoint_stats": endpoint_stats,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self._send_json({
                    "success": False,
                    "error": str(e)
                })
        elif path == '/api/email-usage-stats':
            """Get email API usage statistics - Email Enrichment feature"""
            if not EMAIL_ENRICHMENT_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Email Enrichment not available"
                })
                return

            try:
                stats = email_service.get_api_usage_stats()
                self._send_json({
                    "success": True,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self._send_json({
                    "success": False,
                    "error": str(e)
                })
        elif path == '/api/sheets-leads':
            """Pull leads directly from Google Sheets in real-time"""
            if not SHEETS_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Google Sheets integration not available"
                })
                return

            try:
                # Create client and fetch leads directly from sheet
                sheets_client = GoogleSheetsClient()
                leads = sheets_client.read_all_leads()

                # Add IDs for frontend compatibility
                for idx, lead in enumerate(leads):
                    lead['id'] = idx + 1
                    if 'created_at' not in lead:
                        lead['created_at'] = datetime.now().isoformat()

                self._send_json({
                    "success": True,
                    "source": "google_sheets",
                    "count": len(leads),
                    "leads": leads,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                import traceback
                print(f"Error fetching from sheets: {e}")
                print(traceback.format_exc())
                self._send_json({
                    "success": False,
                    "error": str(e)
                })
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/places-search':
            """Generate real leads using Google Places API with precise location targeting"""
            if not PLACES_API_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Google Places API integration not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            query = data.get('query') or data.get('industry', 'business')
            location = data.get('location', 'San Francisco, CA')  # Use city name instead of coordinates
            max_results = data.get('max_results', 20)

            try:
                # Use enhanced generator for precise location targeting
                generator = EnhancedPlacesLeadGenerator()
                leads = generator.search_businesses_precise(
                    query=query,
                    location=location,
                    max_results=max_results
                )

                # DATA VALIDATION (Phase 1 feature)
                valid_leads = leads
                invalid_count = 0
                if PHASE_1_AVAILABLE:
                    valid_leads, invalid_leads, validation_errors = validate_leads_batch(leads)
                    invalid_count = len(invalid_leads)
                    if invalid_count > 0:
                        print(f"⚠️  {invalid_count} leads failed validation")
                        if logger:
                            logger.warning(f"{invalid_count} leads failed validation")

                # Save to database with location verification
                saved_count = generator.save_to_database(valid_leads)

                # AUTO-SYNC TO GOOGLE SHEETS (Primary Database)
                sheets_synced = 0
                sheets_errors = []
                if SHEETS_AVAILABLE:
                    try:
                        if logger:
                            logger.info(f"Syncing {len(valid_leads)} leads to Google Sheets...")
                        sheets_client = GoogleSheetsClient()
                        sheets_synced = sheets_client.add_leads_to_sheet(valid_leads)
                        print(f"✅ Synced {sheets_synced} leads to Google Sheets")
                        if logger:
                            logger.info(f"Successfully synced {sheets_synced} leads to Google Sheets")
                    except Exception as sheets_error:
                        error_msg = f"Google Sheets sync failed: {str(sheets_error)}"
                        print(f"⚠️  {error_msg}")
                        if logger:
                            logger.error(error_msg)
                        sheets_errors.append(error_msg)
                        # Don't fail the request if sheets sync fails

                self._send_json({
                    "success": True,
                    "query": query,
                    "location": location,
                    "count": len(leads),
                    "valid_count": len(valid_leads),
                    "invalid_count": invalid_count,
                    "saved_to_db": saved_count,
                    "synced_to_sheets": sheets_synced,
                    "sheets_errors": sheets_errors,
                    "leads": leads,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                import traceback
                print(f"Error in places-search: {e}")
                print(traceback.format_exc())
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/scrape':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            industry = data.get('industry') or random.choice(BUSINESS_TYPES)
            location = data.get('location') or random.choice(LOCATIONS)
            max_leads = data.get('max_leads', 20)
            min_score = data.get('min_score', 0)
            save_to_db = data.get('save_to_db', True)

            print(f"Scraping leads for {industry} in {location}...")

            leads = scrape_leads(
                industry=industry,
                location=location,
                max_results=max_leads,
                min_score=min_score,
                save_to_db=save_to_db
            )

            self._send_json({
                "success": True,
                "industry": industry,
                "location": location,
                "count": len(leads),
                "leads": leads,
                "saved_to_db": save_to_db,
                "timestamp": datetime.now().isoformat()
            })

        elif path == '/api/email-discover':
            """Discover email addresses using Hunter.io - Email Enrichment feature"""
            if not EMAIL_ENRICHMENT_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Email Enrichment not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            domain = data.get('domain')
            company = data.get('company')

            if not domain:
                self._send_json({
                    "success": False,
                    "error": "Domain is required"
                })
                return

            try:
                # Use discover_and_validate which finds and validates emails
                success, emails, error = email_service.discover_and_validate(domain, company)

                if success:
                    self._send_json({
                        "success": True,
                        "domain": domain,
                        "company": company,
                        "emails_found": len(emails),
                        "emails": emails,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    self._send_json({
                        "success": False,
                        "error": error
                    })

                if logger:
                    logger.info(f"Email discovery for {domain}: {len(emails) if success else 0} emails found")

            except Exception as e:
                if logger:
                    logger.error(f"Email discovery failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/email-validate':
            """Validate email address using Abstract API - Email Enrichment feature"""
            if not EMAIL_ENRICHMENT_AVAILABLE or not email_service.validator:
                self._send_json({
                    "success": False,
                    "error": "Email validation not available (Abstract API not configured)"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            email = data.get('email')

            if not email:
                self._send_json({
                    "success": False,
                    "error": "Email address is required"
                })
                return

            try:
                success, validation_data, error = email_service.validator.validate_email(email)

                if success:
                    self._send_json({
                        "success": True,
                        "email": email,
                        "validation": validation_data,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    self._send_json({
                        "success": False,
                        "error": error
                    })

                if logger:
                    logger.info(f"Email validation for {email}: {validation_data.get('status', 'unknown')}")

            except Exception as e:
                if logger:
                    logger.error(f"Email validation failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/bulk-email-discover':
            """Bulk email discovery for multiple domains - Email Enrichment feature"""
            if not EMAIL_ENRICHMENT_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Email Enrichment not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            domains = data.get('domains', [])
            companies = data.get('companies', [])

            if not domains:
                self._send_json({
                    "success": False,
                    "error": "Domains list is required"
                })
                return

            try:
                results = email_service.bulk_discover(domains, companies)

                total_emails = sum(len(emails) for emails in results.values())
                domains_with_emails = sum(1 for emails in results.values() if emails)

                self._send_json({
                    "success": True,
                    "total_domains": len(domains),
                    "domains_with_emails": domains_with_emails,
                    "total_emails_found": total_emails,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                })

                if logger:
                    logger.info(f"Bulk email discovery: {total_emails} emails found for {len(domains)} domains")

            except Exception as e:
                if logger:
                    logger.error(f"Bulk email discovery failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/sync-to-sheets':
            """Sync discovered emails from database to Google Sheets"""
            if not SHEETS_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Google Sheets integration not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            limit = data.get('limit', None)

            try:
                from sync_to_sheets import GoogleSheetsSync

                sync = GoogleSheetsSync()
                result = sync.sync_emails_to_sheets(limit=limit)

                self._send_json(result)

                if logger:
                    logger.info(f"Sync to sheets: {result.get('synced', 0)} emails synced")

            except Exception as e:
                if logger:
                    logger.error(f"Sync to sheets failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/leads/batch/find-email':
            """Batch find emails for leads - Frontend compatibility endpoint"""
            if not EMAIL_ENRICHMENT_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Email Enrichment not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            lead_ids = data.get('lead_ids', [])

            if not lead_ids:
                self._send_json({
                    "success": False,
                    "error": "No lead IDs provided"
                })
                return

            try:
                # Get leads from database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                placeholders = ','.join(['?' for _ in lead_ids])
                cursor.execute(f'SELECT id, business_name, website FROM leads WHERE id IN ({placeholders})', lead_ids)
                leads_data = cursor.fetchall()
                conn.close()

                if not leads_data:
                    self._send_json({
                        "success": False,
                        "error": "No leads found"
                    })
                    return

                # Extract domains from websites
                domains = []
                companies = []
                lead_to_domain = {}

                for lead_id, business_name, website in leads_data:
                    if website:
                        # Extract domain from URL
                        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                        if domain:
                            domains.append(domain)
                            companies.append(business_name)
                            lead_to_domain[domain] = lead_id

                if not domains:
                    self._send_json({
                        "success": False,
                        "error": "No valid domains found"
                    })
                    return

                # Discover emails for domains
                results = email_service.bulk_discover(domains, companies)

                # Update leads with discovered emails
                updated_count = 0
                total_emails_found = 0

                for domain, emails in results.items():
                    if emails and len(emails) > 0:
                        lead_id = lead_to_domain.get(domain)
                        if lead_id:
                            # Update lead with first discovered email
                            primary_email = emails[0]
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE leads SET email = ? WHERE id = ?', (primary_email['email'], lead_id))
                            conn.commit()
                            conn.close()
                            updated_count += 1
                            total_emails_found += len(emails)

                self._send_json({
                    "success": True,
                    "total": len(lead_ids),
                    "processed": len(leads_data),
                    "updated": updated_count,
                    "emails_found": total_emails_found,
                    "message": f"Found emails for {updated_count} leads"
                })

                if logger:
                    logger.info(f"Batch find email: {updated_count}/{len(lead_ids)} leads updated with {total_emails_found} emails")

            except Exception as e:
                if logger:
                    logger.error(f"Batch find email failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        elif path == '/api/leads/batch/validate-email':
            """Batch validate emails for leads - Frontend compatibility endpoint"""
            if not EMAIL_ENRICHMENT_AVAILABLE:
                self._send_json({
                    "success": False,
                    "error": "Email Enrichment not available"
                })
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            lead_ids = data.get('lead_ids', [])

            if not lead_ids:
                self._send_json({
                    "success": False,
                    "error": "No lead IDs provided"
                })
                return

            try:
                # Get leads with emails from database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                placeholders = ','.join(['?' for _ in lead_ids])
                cursor.execute(f'SELECT id, email FROM leads WHERE id IN ({placeholders}) AND email IS NOT NULL', lead_ids)
                leads_data = cursor.fetchall()
                conn.close()

                if not leads_data:
                    self._send_json({
                        "success": False,
                        "error": "No leads with emails found"
                    })
                    return

                validated_count = 0
                valid_count = 0

                for lead_id, email in leads_data:
                    # Validate email using Hunter.io
                    if email_service.hunter:
                        success, validation_data, error = email_service.hunter.verify_email(email)

                        if success and validation_data.get('status') == 'valid':
                            valid_count += 1
                            validated_count += 1

                            # Update lead with validation status
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            # Note: Would need to add email_validation_status column to schema
                            # cursor.execute('UPDATE leads SET email_validation_status = ? WHERE id = ?', ('valid', lead_id))
                            conn.commit()
                            conn.close()
                        else:
                            validated_count += 1

                self._send_json({
                    "success": True,
                    "total": len(lead_ids),
                    "processed": len(leads_data),
                    "validated": validated_count,
                    "valid": valid_count,
                    "message": f"Validated {validated_count} emails, {valid_count} are valid"
                })

                if logger:
                    logger.info(f"Batch validate email: {validated_count} emails validated, {valid_count} valid")

            except Exception as e:
                if logger:
                    logger.error(f"Batch validate email failed: {e}")
                self._send_json({
                    "success": False,
                    "error": str(e)
                })

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_PUT(self):
        """Handle PUT requests for updating lead status"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Extract lead ID from path
        # Expected format: /api/leads/{id}/status or /api/leads/{id}
        parts = path.split('/')
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads':
            try:
                lead_id = int(parts[3])

                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                if 'status' in data:
                    # Update lead status
                    new_status = data['status']
                    update_lead_status(lead_id, new_status)

                    self._send_json({
                        "success": True,
                        "message": f"Lead {lead_id} updated to {new_status}"
                    })
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'Bad Request: Missing status field')
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Bad Request: Invalid lead ID')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_DELETE(self):
        """Handle DELETE requests for removing leads"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Extract lead ID from path
        # Expected format: /api/leads/{id}
        parts = path.split('/')
        if len(parts) >= 4 and parts[1] == 'api' and parts[2] == 'leads':
            try:
                lead_id = int(parts[3])

                # Delete lead from database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
                conn.commit()
                rows_affected = cursor.rowcount
                conn.close()

                if rows_affected > 0:
                    self._send_json({
                        "success": True,
                        "message": f"Lead {lead_id} deleted"
                    })
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Lead not found')
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Bad Request: Invalid lead ID')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        """Enhanced logging to both console and log file"""
        message = format % args
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        if logger:
            logger.info(message)

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, LeadForgeHandler)

    print("=" * 60)
    print("🚀 LeadForge AI Real-Time Scraper")
    print("=" * 60)
    print(f"✅ Server running on: http://localhost:{port}")
    print(f"📖 API Documentation: http://localhost:{port}/")
    print("=" * 60)

    # Show Phase 1 features
    if PHASE_1_AVAILABLE:
        print("\n🛡️  PHASE 1 FEATURES ACTIVE:")
        print("  ✅ Data Validation")
        print("  ✅ Error Handling & Retry Logic")
        print("  ✅ Health Monitoring")
        print("  ✅ Enhanced Logging")
        print(f"  📝 Log file: leadforge.log")
        print(f"  🏥 Health check: http://localhost:{port}/api/health")
        print("=" * 60)

    # Show Phase 2 features
    if PHASE_2_AVAILABLE:
        print("\n🚀 PHASE 2 FEATURES ACTIVE:")
        print("  ✅ Rate Limiting & Throttling")
        print("  ✅ Automated Backups")
        print("  ✅ Idempotent Operations")
        print(f"  💾 Backup trigger: http://localhost:{port}/api/backup")
        print(f"  📊 Backup stats: http://localhost:{port}/api/backup-stats")
        print(f"  ⏱️  Rate limit stats: http://localhost:{port}/api/rate-limit-stats")
        print("=" * 60)

    # Show Email Enrichment features
    if EMAIL_ENRICHMENT_AVAILABLE:
        print("\n📧 EMAIL ENRICHMENT ACTIVE:")
        print("  ✅ Hunter.io Email Discovery")
        print("  ✅ Abstract API Email Validation")
        print(f"  🔍 Email discovery: POST http://localhost:{port}/api/email-discover")
        print(f"  ✅ Email validation: POST http://localhost:{port}/api/email-validate")
        print(f"  📊 Email API usage: GET http://localhost:{port}/api/email-usage-stats")
        print("=" * 60)

    print("\n📋 Available Endpoints:")
    print("  GET  /                         - Server info")
    print("  POST /api/places-search        - Generate real leads")
    print("  GET  /api/leads                - Get saved leads")
    print("  GET  /api/sheets-leads         - Load from Google Sheets")
    print("  GET  /api/health               - Health check (Phase 1)")
    print("  GET  /api/backup               - Trigger backup (Phase 2)")
    print("  GET  /api/backup-stats         - Backup statistics (Phase 2)")
    print("  GET  /api/rate-limit-stats     - Rate limit stats (Phase 2)")
    if EMAIL_ENRICHMENT_AVAILABLE:
        print("  POST /api/email-discover       - Discover emails (Hunter.io)")
        print("  POST /api/email-validate       - Validate emails (Abstract API)")
        print("  POST /api/bulk-email-discover  - Bulk email discovery")
        print("  GET  /api/email-usage-stats    - Email API usage stats")
    print("  GET  /api/test                  - Test connection")
    print("\n💡 Open the frontend HTML file in your browser to start scraping!")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")

    if logger:
        logger.info("LeadForge AI server starting")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        if logger:
            logger.info("LeadForge AI server stopped")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
