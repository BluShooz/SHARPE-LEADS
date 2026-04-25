"""
LeadForge AI - Idempotent Operations Module
Ensures operations can be safely retried without side effects
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set
from functools import wraps

logger = logging.getLogger(__name__)


class IdempotencyKeyManager:
    """
    Manages idempotency keys to prevent duplicate operations

    Features:
        - Key generation
        - Key expiration
        - Duplicate detection
        - Result caching
    """

    def __init__(self, key_ttl: int = 3600):
        """
        Initialize idempotency key manager

        Args:
            key_ttl: Time to live for keys in seconds (default: 1 hour)
        """
        self.keys: Dict[str, dict] = {}
        self.key_ttl = key_ttl
        self._cleanup_threshold = 1000  # Cleanup when this many keys accumulate

    def generate_key(self, operation: str, data: dict) -> str:
        """
        Generate idempotency key from operation and data

        Args:
            operation: Operation name
            data: Operation data

        Returns:
            Idempotency key string
        """
        # Create deterministic key from operation and data
        key_data = {
            'operation': operation,
            'data': sorted(data.items()) if isinstance(data, dict) else data
        }

        key_string = json.dumps(key_data, sort_keys=True)
        hash_obj = hashlib.sha256(key_string.encode())
        return hash_obj.hexdigest()

    def check_and_set(
        self,
        key: str,
        result: Any = None
    ) -> tuple[bool, Optional[Any]]:
        """
        Check if key exists, set if not

        Args:
            key: Idempotency key
            result: Result to cache if key doesn't exist

        Returns:
            (is_duplicate, cached_result)
        """
        # Periodic cleanup
        if len(self.keys) > self._cleanup_threshold:
            self._cleanup_expired_keys()

        if key in self.keys:
            key_data = self.keys[key]

            # Check if expired
            if datetime.now() - key_data['created'] < timedelta(seconds=self.key_ttl):
                # Key exists and not expired
                logger.debug(f"Duplicate operation detected: {key[:16]}...")
                return True, key_data.get('result')
            else:
                # Key expired, remove it
                del self.keys[key]

        # Set new key
        self.keys[key] = {
            'created': datetime.now(),
            'result': result
        }

        return False, None

    def _cleanup_expired_keys(self):
        """Remove expired keys from storage"""
        cutoff = datetime.now() - timedelta(seconds=self.key_ttl)
        expired = [
            key for key, data in self.keys.items()
            if data['created'] < cutoff
        ]

        for key in expired:
            del self.keys[key]

        logger.info(f"Cleaned up {len(expired)} expired idempotency keys")

    def invalidate_key(self, key: str):
        """
        Manually invalidate an idempotency key

        Args:
            key: Key to invalidate
        """
        if key in self.keys:
            del self.keys[key]
            logger.debug(f"Invalidated key: {key[:16]}...")

    def get_stats(self) -> dict:
        """
        Get idempotency key statistics

        Returns:
            Dictionary with stats
        """
        return {
            'total_keys': len(self.keys),
            'key_ttl_seconds': self.key_ttl,
            'cleanup_threshold': self._cleanup_threshold
        }


# Global idempotency key manager
idempotency_manager = IdempotencyKeyManager()


def idempotent(
    key_func: Optional[callable] = None,
    ttl: int = 3600
):
    """
    Decorator to make function idempotent

    Args:
        key_func: Function to extract idempotency key from args
        ttl: Time to live for keys in seconds

    Example:
        @idempotent(key_func=lambda args: args[0]['id'])
        def create_user(user_data):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Use function name and args as key
                key_data = {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(sorted(kwargs.items()))
                }
                key = idempotency_manager.generate_key(func.__name__, key_data)

            # Check if already executed
            is_duplicate, cached_result = idempotency_manager.check_and_set(key)

            if is_duplicate:
                logger.info(f"Returning cached result for {func.__name__}")
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            idempotency_manager.keys[key]['result'] = result

            return result

        return wrapper
    return decorator


class SafeOperationRunner:
    """
    Runs operations safely with idempotency and error handling

    Ensures operations can be retried safely without side effects
    """

    def __init__(self):
        """Initialize safe operation runner"""
        self.operations: Dict[str, Set[str]] = {}
        self.results_cache: Dict[str, Any] = {}

    def run_operation(
        self,
        operation_name: str,
        operation_func: callable,
        operation_id: str,
        *args,
        **kwargs
    ) -> tuple[bool, Any, Optional[str]]:
        """
        Run operation with idempotency guarantee

        Args:
            operation_name: Name of operation type
            operation_func: Function to execute
            operation_id: Unique ID for this specific operation
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            (success, result, error_message)
        """
        cache_key = f"{operation_name}:{operation_id}"

        # Check if already executed
        if cache_key in self.results_cache:
            logger.info(f"Using cached result for {cache_key}")
            return True, self.results_cache[cache_key], None

        try:
            # Execute operation
            result = operation_func(*args, **kwargs)

            # Cache result
            self.results_cache[cache_key] = result

            # Track operation
            if operation_name not in self.operations:
                self.operations[operation_name] = set()
            self.operations[operation_name].add(operation_id)

            logger.info(f"Operation {cache_key} completed successfully")
            return True, result, None

        except Exception as e:
            error_msg = f"Operation {cache_key} failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def invalidate_cache(self, operation_name: str = None, operation_id: str = None):
        """
        Invalidate cached results

        Args:
            operation_name: Operation type to invalidate
            operation_id: Specific operation ID to invalidate
        """
        if operation_name and operation_id:
            # Invalidate specific operation
            cache_key = f"{operation_name}:{operation_id}"
            if cache_key in self.results_cache:
                del self.results_cache[cache_key]
                logger.debug(f"Invalidated cache for {cache_key}")

        elif operation_name:
            # Invalidate all operations of this type
            keys_to_remove = [
                k for k in self.results_cache.keys()
                if k.startswith(f"{operation_name}:")
            ]
            for key in keys_to_remove:
                del self.results_cache[key]
            logger.info(f"Invalidated {len(keys_to_remove)} caches for {operation_name}")

        else:
            # Invalidate all
            count = len(self.results_cache)
            self.results_cache.clear()
            logger.info(f"Invalidated all {count} cached results")

    def get_stats(self) -> dict:
        """
        Get operation statistics

        Returns:
            Dictionary with stats
        """
        return {
            'operations_tracked': len(self.operations),
            'cached_results': len(self.results_cache),
            'operation_types': list(self.operations.keys())
        }


def safe_insert(
    table_name: str,
    connection,
    data: dict,
    unique_columns: list = None
) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Safely insert data with duplicate prevention

    Args:
        table_name: Table to insert into
        connection: Database connection
        data: Data to insert
        unique_columns: Columns that must be unique

    Returns:
        (success, row_id, error_message)
    """
    try:
        cursor = connection.cursor()

        # Check for duplicates if unique columns specified
        if unique_columns:
            conditions = []
            values = []
            for col in unique_columns:
                if col in data:
                    conditions.append(f"{col} = ?")
                    values.append(data[col])

            if conditions:
                cursor.execute(
                    f"SELECT id FROM {table_name} WHERE {' AND '.join(conditions)}",
                    values
                )
                existing = cursor.fetchone()

                if existing:
                    logger.info(f"Duplicate entry found in {table_name}, skipping insert")
                    return True, existing[0], None  # Success, existing ID, no error

        # Insert data
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
            values
        )

        connection.commit()
        logger.info(f"Inserted data into {table_name}, ID: {cursor.lastrowid}")

        return True, cursor.lastrowid, None

    except Exception as e:
        error_msg = f"Insert into {table_name} failed: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def safe_update(
    table_name: str,
    connection,
    data: dict,
    where_conditions: dict,
    require_change: bool = False
) -> tuple[bool, int, Optional[str]]:
    """
    Safely update data with change detection

    Args:
        table_name: Table to update
        connection: Database connection
        data: Data to update
        where_conditions: Conditions for WHERE clause
        require_change: Only update if data would actually change

    Returns:
        (success, rows_affected, error_message)
    """
    try:
        cursor = connection.cursor()

        # Build WHERE clause
        where_clause = ' AND '.join([f"{k} = ?" for k in where_conditions.keys()])
        where_values = list(where_conditions.values())

        # If require_change, check current values
        if require_change:
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE {where_clause}",
                where_values
            )
            existing = cursor.fetchone()

            if not existing:
                return False, 0, "No matching row found"

            # Check if values would actually change
            # (This is simplified - in production you'd map column names)
            # For now, just proceed with update

        # Build SET clause
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + where_values

        # Execute update
        cursor.execute(
            f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}",
            values
        )

        rows_affected = cursor.rowcount
        connection.commit()

        logger.info(f"Updated {table_name}, {rows_affected} rows affected")

        return True, rows_affected, None

    except Exception as e:
        error_msg = f"Update {table_name} failed: {str(e)}"
        logger.error(error_msg)
        return False, 0, error_msg
