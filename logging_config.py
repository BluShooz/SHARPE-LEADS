"""
LeadForge AI - Logging Configuration Module
Centralized logging setup for all components
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = 'INFO',
    log_file: str = 'leadforge.log',
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True
) -> None:
    """
    Setup logging configuration for the entire application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
        enable_console: Whether to output logs to console
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # Log startup
    logger.info("=" * 60)
    logger.info("LeadForge AI Logging Initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class OperationLogger:
    """
    Context manager for logging operations

    Example:
        with OperationLogger("fetch_leads", {"query": "restaurants"}):
            results = fetch_leads("restaurants")
    """

    def __init__(self, operation: str, details: dict = None, log_level: str = 'INFO'):
        """
        Initialize operation logger

        Args:
            operation: Operation name
            details: Additional details to log
            log_level: Logging level
        """
        self.operation = operation
        self.details = details or {}
        self.log_level = getattr(logging, log_level.upper())
        self.logger = logging.getLogger(__name__)
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        details_str = ', '.join(f'{k}={v}' for k, v in self.details.items())
        self.logger.log(self.log_level, f"Starting: {self.operation} ({details_str})")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.log(
                self.log_level,
                f"Completed: {self.operation} in {duration:.2f}s"
            )
        else:
            self.logger.error(
                f"Failed: {self.operation} after {duration:.2f}s - {exc_val}"
            )
        return False  # Don't suppress exceptions


def log_function_call(func):
    """
    Decorator to log function calls

    Example:
        @log_function_call
        def my_function(arg1, arg2):
            pass
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        args_str = ', '.join(str(arg) for arg in args)
        kwargs_str = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))

        logger.debug(f"Calling {func.__name__}({all_args})")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


# Performance monitoring
class PerformanceMonitor:
    """Monitor and log performance metrics"""

    def __init__(self, operation_name: str):
        """
        Initialize performance monitor

        Args:
            operation_name: Name of operation being monitored
        """
        self.operation_name = operation_name
        self.logger = logging.getLogger(__name__)
        self.metrics = {}

    def track_metric(self, metric_name: str, value: float, unit: str = 'count'):
        """
        Track a performance metric

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        self.metrics[metric_name] = {'value': value, 'unit': unit}

    def log_metrics(self):
        """Log all tracked metrics"""
        if not self.metrics:
            return

        metrics_str = ', '.join(
            f'{name}={data["value"]}{data["unit"]}'
            for name, data in self.metrics.items()
        )
        self.logger.info(f"{self.operation_name} metrics: {metrics_str}")
