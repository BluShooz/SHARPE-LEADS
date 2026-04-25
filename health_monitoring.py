"""
LeadForge AI - Health Monitoring Module
Monitors system health and detects issues before they become problems
"""

import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    message: str
    details: Dict = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class HealthMonitor:
    """
    Monitors system health and generates alerts

    Checks:
        - Backend API
        - Database connectivity
        - Google Sheets API
        - Google Places API
        - Disk space
        - Memory usage
        - Recent errors
    """

    def __init__(self, db_path: str):
        """
        Initialize health monitor

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.alerts = []
        self.last_check = None

    def check_database(self) -> HealthCheckResult:
        """Check database connectivity and health"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if database is accessible
            cursor.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]

            # Check database size
            size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB

            # Check last write time
            last_write = datetime.fromtimestamp(os.path.getmtime(self.db_path))
            hours_since_write = (datetime.now() - last_write).total_seconds() / 3600

            conn.close()

            status = 'healthy'
            messages = [f"Database contains {count} leads", f"Size: {size:.1f}MB"]

            if hours_since_write > 24:
                status = 'degraded'
                messages.append(f"Warning: No writes in {hours_since_write:.0f} hours")

            return HealthCheckResult(
                name='database',
                status=status,
                message='. '.join(messages),
                details={
                    'lead_count': count,
                    'size_mb': round(size, 2),
                    'hours_since_write': round(hours_since_write, 1)
                }
            )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                name='database',
                status='unhealthy',
                message=f"Database error: {str(e)}",
                details={'error': str(e)}
            )

    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        try:
            stat = os.statvfs(os.path.dirname(self.db_path))
            total = stat.f_frsize * stat.f_blocks
            available = stat.f_frsize * stat.f_bavail
            used = total - available
            percent_used = (used / total) * 100

            status = 'healthy'
            if percent_used > 90:
                status = 'unhealthy'
            elif percent_used > 75:
                status = 'degraded'

            return HealthCheckResult(
                name='disk_space',
                status=status,
                message=f"Disk usage: {percent_used:.1f}%",
                details={
                    'total_gb': round(total / (1024**3), 2),
                    'available_gb': round(available / (1024**3), 2),
                    'percent_used': round(percent_used, 1)
                }
            )

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return HealthCheckResult(
                name='disk_space',
                status='unhealthy',
                message=f"Disk check error: {str(e)}"
            )

    def check_google_sheets(self) -> HealthCheckResult:
        """Check Google Sheets API connectivity"""
        try:
            from google_sheets_integration import GoogleSheetsClient

            client = GoogleSheetsClient()

            if not client.worksheet:
                return HealthCheckResult(
                    name='google_sheets',
                    status='unhealthy',
                    message='Google Sheets not connected'
                )

            # Try to read a small sample
            start = datetime.now()
            leads = client.read_all_leads()
            duration = (datetime.now() - start).total_seconds()

            status = 'healthy'
            if duration > 5:
                status = 'degraded'

            return HealthCheckResult(
                name='google_sheets',
                status=status,
                message=f"Connected, {len(leads)} leads, {duration:.2f}s response time",
                details={
                    'lead_count': len(leads),
                    'response_time_seconds': round(duration, 2)
                }
            )

        except ImportError:
            return HealthCheckResult(
                name='google_sheets',
                status='degraded',
                message='Google Sheets integration not available'
            )
        except Exception as e:
            logger.error(f"Google Sheets health check failed: {e}")
            return HealthCheckResult(
                name='google_sheets',
                status='unhealthy',
                message=f"Google Sheets error: {str(e)}"
            )

    def check_google_places_api(self) -> HealthCheckResult:
        """Check Google Places API connectivity"""
        try:
            import requests

            API_KEY = "AIzaSyCTrX9ySn-2nAZLq3SkadPAD0Cmp202oXk"
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": "test",
                "key": API_KEY
            }

            start = datetime.now()
            response = requests.get(url, params=params, timeout=10)
            duration = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'UNKNOWN')

                if status == 'OK':
                    return HealthCheckResult(
                        name='google_places_api',
                        status='healthy',
                        message=f'API working, {duration:.2f}s response time',
                        details={
                            'response_time_seconds': round(duration, 2),
                            'api_status': status
                        }
                    )
                elif status == 'ZERO_RESULTS':
                    return HealthCheckResult(
                        name='google_places_api',
                        status='healthy',
                        message='API working (test query returned no results)',
                        details={
                            'response_time_seconds': round(duration, 2),
                            'api_status': status
                        }
                    )
                elif status == 'OVER_QUERY_LIMIT':
                    return HealthCheckResult(
                        name='google_places_api',
                        status='unhealthy',
                        message='API quota exceeded',
                        details={'api_status': status}
                    )
                else:
                    return HealthCheckResult(
                        name='google_places_api',
                        status='degraded',
                        message=f'API status: {status}',
                        details={'api_status': status}
                    )
            else:
                return HealthCheckResult(
                    name='google_places_api',
                    status='unhealthy',
                    message=f'HTTP {response.status_code}',
                    details={'status_code': response.status_code}
                )

        except requests.Timeout:
            return HealthCheckResult(
                name='google_places_api',
                status='unhealthy',
                message='Request timeout'
            )
        except Exception as e:
            logger.error(f"Google Places API health check failed: {e}")
            return HealthCheckResult(
                name='google_places_api',
                status='unhealthy',
                message=f"API error: {str(e)}"
            )

    def check_recent_errors(self) -> HealthCheckResult:
        """Check for recent errors in logs"""
        try:
            log_file = 'leadforge.log'

            if not os.path.exists(log_file):
                return HealthCheckResult(
                    name='recent_errors',
                    status='healthy',
                    message='No log file found'
                )

            # Check last 100 lines for errors
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]

            error_count = sum(1 for line in lines if 'ERROR' in line.upper())

            status = 'healthy'
            if error_count > 10:
                status = 'unhealthy'
            elif error_count > 5:
                status = 'degraded'

            return HealthCheckResult(
                name='recent_errors',
                status=status,
                message=f'{error_count} errors in last 100 log lines',
                details={'error_count': error_count}
            )

        except Exception as e:
            logger.error(f"Error log check failed: {e}")
            return HealthCheckResult(
                name='recent_errors',
                status='unhealthy',
                message=f"Log check error: {str(e)}"
            )

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks

        Returns:
            Dictionary of check results
        """
        logger.info("Running health checks...")

        results = {
            'database': self.check_database(),
            'disk_space': self.check_disk_space(),
            'google_sheets': self.check_google_sheets(),
            'google_places_api': self.check_google_places_api(),
            'recent_errors': self.check_recent_errors()
        }

        self.last_check = datetime.now()

        # Generate alerts for unhealthy services
        for name, result in results.items():
            if result.status == 'unhealthy':
                alert = f"ALERT: {name} is unhealthy - {result.message}"
                self.alerts.append(alert)
                logger.error(alert)

        logger.info(f"Health checks complete: {sum(1 for r in results.values() if r.status == 'healthy')}/{len(results)} healthy")

        return results

    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> str:
        """
        Get overall system status

        Args:
            results: Health check results

        Returns:
            Overall status: 'healthy', 'degraded', or 'unhealthy'
        """
        statuses = [r.status for r in results.values()]

        if 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'degraded' in statuses:
            return 'degraded'
        else:
            return 'healthy'

    def get_health_report(self) -> Dict:
        """
        Get complete health report

        Returns:
            Health report dictionary
        """
        results = self.run_all_checks()

        return {
            'overall_status': self.get_overall_status(results),
            'checks': {name: {
                'status': result.status,
                'message': result.message,
                'details': result.details,
                'timestamp': result.timestamp
            } for name, result in results.items()},
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'alerts': self.alerts[-10:]  # Last 10 alerts
        }
