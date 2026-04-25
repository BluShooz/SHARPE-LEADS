"""
LeadForge AI - Automated Backups Module
Performs automated backups of database and critical data
"""

import os
import sqlite3
import shutil
import gzip
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages automated backups with retention policies

    Features:
        - Database backups
        - Google Sheets export backups
        - Log file backups
        - Configurable retention policies
        - Automatic cleanup of old backups
    """

    def __init__(
        self,
        db_path: str,
        backup_dir: str = "backups",
        retention_days: int = 7
    ):
        """
        Initialize backup manager

        Args:
            db_path: Path to SQLite database
            backup_dir: Directory to store backups
            retention_days: Days to keep backups
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.retention_days = retention_days
        self.backup_counts = {
            'database': 0,
            'sheets': 0,
            'logs': 0
        }

        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_database(self, compress: bool = True) -> Optional[str]:
        """
        Backup SQLite database

        Args:
            compress: Whether to compress the backup

        Returns:
            Path to backup file or None on failure
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"leads_db_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Use SQLite's .dump command
            conn = sqlite3.connect(self.db_path)

            with open(backup_path, 'w') as f:
                for line in conn.iterdump():
                    f.write('%s\n' % line)

            conn.close()

            # Compress if requested
            if compress:
                compressed_path = backup_path + '.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove uncompressed backup
                os.remove(backup_path)
                backup_path = compressed_path

            file_size = os.path.getsize(backup_path) / 1024  # KB
            logger.info(f"Database backed up: {backup_path} ({file_size:.1f} KB)")
            self.backup_counts['database'] += 1

            return backup_path

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None

    def backup_logs(self, max_files: int = 5) -> int:
        """
        Backup and rotate log files

        Args:
            max_files: Maximum number of log backups to keep

        Returns:
            Number of log files backed up
        """
        try:
            log_files = [
                'leadforge.log',
                'leadforge.log.1',
                'leadforge.log.2',
                'leadforge.log.3',
                'leadforge.log.4'
            ]

            backed_up = 0
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for log_file in log_files:
                if os.path.exists(log_file):
                    backup_name = f"{log_file}.{timestamp}"
                    backup_path = os.path.join(self.backup_dir, backup_name)
                    shutil.copy2(log_file, backup_path)
                    backed_up += 1

            logger.info(f"Backed up {backed_up} log files")
            self.backup_counts['logs'] += backed_up

            return backed_up

        except Exception as e:
            logger.error(f"Log backup failed: {e}")
            return 0

    def export_google_sheets_to_csv(self, sheets_client) -> Optional[str]:
        """
        Export Google Sheets data to CSV backup with professional lead management fields

        Args:
            sheets_client: GoogleSheetsClient instance

        Returns:
            Path to CSV backup or None on failure
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"leads_export_{timestamp}.csv"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Get all leads from sheets
            leads = sheets_client.read_all_leads()

            # Write to CSV with professional lead management fields
            with open(backup_path, 'w', encoding='utf-8') as f:
                # Professional header - essential fields first, then nice-to-haves
                header = ','.join([
                    'Business Name',           # Essential
                    'Contact Name',           # Essential
                    'Phone',                  # Essential
                    'Email',                  # Essential
                    'Website',                # Essential
                    'Location',               # Essential
                    'Industry',               # Essential
                    'Source',                 # Essential
                    'Status',                 # Essential
                    'Stage',                  # Essential
                    'Priority Score',         # Already there
                    'Rating',                 # Nice to have
                    'Reviews',                # Nice to have
                    'Business Hours',         # Essential
                    'Last Contact Date',      # Essential
                    'Next Action',            # Essential
                    'Owner Name',             # Nice to have
                    'Estimated Value',       # Nice to have
                    'Facebook',               # Nice to have
                    'Instagram',              # Nice to have
                    'LinkedIn',               # Nice to have
                    'Tags',                   # Nice to have
                    'Notes',                  # Nice to have
                    'Date Added',             # Nice to have
                    'Last Updated'            # Nice to have
                ])
                f.write(header + '\n')

                # Write data for each lead
                for lead in leads:
                    row = [
                        f'"{lead.get("business_name", "")}"',
                        f'"{lead.get("contact_name", "")}"',
                        f'"{lead.get("phone", "")}"',
                        f'"{lead.get("email", "")}"',
                        f'"{lead.get("website", "")}"',
                        f'"{lead.get("location", "")}"',
                        f'"{lead.get("industry", "")}"',
                        f'"{lead.get("source", "Google Places")}"',
                        f'"{lead.get("status", "new")}"',
                        f'"{lead.get("stage", "PROSPECT")}"',
                        f'{lead.get("score", 0)}',
                        f'{lead.get("rating", "") or ""}',
                        f'{lead.get("reviews_count", "") or ""}',
                        f'"{lead.get("business_hours", "")}"',
                        f'"{lead.get("last_contact_date", "")}"',
                        f'"{lead.get("next_action", "")}"',
                        f'"{lead.get("owner_name", "")}"',
                        f'"{lead.get("estimated_value", "")}"',
                        f'"{lead.get("facebook", "")}"',
                        f'"{lead.get("instagram", "")}"',
                        f'"{lead.get("linkedin", "")}"',
                        f'"{lead.get("tags", "")}"',
                        f'"{lead.get("notes", "")}"',
                        f'"{lead.get("created_at", "")}"',
                        f'"{lead.get("last_updated", datetime.now().isoformat())}"'
                    ]
                    f.write(','.join(row) + '\n')

            file_size = os.path.getsize(backup_path) / 1024  # KB
            logger.info(f"Professional leads export: {backup_path} ({file_size:.1f} KB, {len(leads)} leads)")
            self.backup_counts['sheets'] += 1

            return backup_path

        except Exception as e:
            logger.error(f"Professional CSV export failed: {e}")
            return None

    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period

        Returns:
            Number of backups removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed = 0

            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)

                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if mtime < cutoff_date:
                    os.remove(file_path)
                    removed += 1
                    logger.info(f"Removed old backup: {filename}")

            logger.info(f"Cleanup complete: removed {removed} old backups")
            return removed

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0

    def get_backup_stats(self) -> dict:
        """
        Get statistics about backups

        Returns:
            Dictionary with backup statistics
        """
        try:
            backup_files = [
                f for f in os.listdir(self.backup_dir)
                if os.path.isfile(os.path.join(self.backup_dir, f))
            ]

            total_size = sum(
                os.path.getsize(os.path.join(self.backup_dir, f))
                for f in backup_files
            ) / (1024 * 1024)  # MB

            # Count by type
            db_backups = sum(1 for f in backup_files if f.startswith('leads_db_'))
            sheet_backups = sum(1 for f in backup_files if f.startswith('sheets_export_'))
            log_backups = sum(1 for f in backup_files if 'log' in f)

            return {
                'total_files': len(backup_files),
                'total_size_mb': round(total_size, 2),
                'database_backups': db_backups,
                'sheets_backups': sheet_backups,
                'log_backups': log_backups,
                'retention_days': self.retention_days,
                'backup_dir': self.backup_dir
            }

        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {}

    def run_full_backup(self, sheets_client=None) -> dict:
        """
        Run complete backup of all data

        Args:
            sheets_client: Optional GoogleSheetsClient for sheets backup

        Returns:
            Dictionary with backup results
        """
        logger.info("Starting full backup...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'database': None,
            'sheets': None,
            'logs': 0,
            'cleanup': 0,
            'success': False
        }

        try:
            # Backup database
            results['database'] = self.backup_database(compress=True)

            # Backup Google Sheets if client provided
            if sheets_client:
                results['sheets'] = self.export_google_sheets_to_csv(sheets_client)

            # Backup logs
            results['logs'] = self.backup_logs()

            # Cleanup old backups
            results['cleanup'] = self.cleanup_old_backups()

            results['success'] = True
            logger.info("Full backup completed successfully")

        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            results['error'] = str(e)

        return results


class BackupScheduler:
    """
    Schedules automated backups at regular intervals

    Can run in background thread or be triggered manually
    """

    def __init__(self, backup_manager: BackupManager):
        """
        Initialize backup scheduler

        Args:
            backup_manager: BackupManager instance
        """
        self.backup_manager = backup_manager
        self.scheduled_backups = {}

    def schedule_daily_backup(self, hour: int = 2, minute: int = 0):
        """
        Schedule daily backup at specific time

        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        self.scheduled_backups['daily'] = {
            'type': 'daily',
            'hour': hour,
            'minute': minute
        }
        logger.info(f"Scheduled daily backup at {hour:02d}:{minute:02d}")

    def schedule_hourly_backup(self):
        """Schedule hourly backup"""
        self.scheduled_backups['hourly'] = {
            'type': 'hourly'
        }
        logger.info("Scheduled hourly backup")

    def should_run_backup(self, backup_type: str) -> bool:
        """
        Check if backup should run based on schedule

        Args:
            backup_type: Type of backup ('daily' or 'hourly')

        Returns:
            True if backup should run
        """
        if backup_type not in self.scheduled_backups:
            return False

        schedule = self.scheduled_backups[backup_type]
        now = datetime.now()

        if schedule['type'] == 'daily':
            # Check if we're at the scheduled time
            scheduled_time = now.replace(
                hour=schedule['hour'],
                minute=schedule['minute'],
                second=0,
                microsecond=0
            )
            # Allow 1 minute window
            return (now - scheduled_time).total_seconds() < 60

        elif schedule['type'] == 'hourly':
            # Run every hour at :00
            return now.minute == 0 and now.second < 10

        return False
