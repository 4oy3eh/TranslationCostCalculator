"""
Translation Cost Calculator - Logging Configuration

Complete logging setup and configuration for the application with
file rotation, multiple handlers, and proper formatting.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from config.settings import Settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Apply color to levelname
        original_levelname = record.levelname
        record.levelname = f"{color}{record.levelname}{reset}"
        
        # Format the record
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return formatted


def setup_logging(console_output: Optional[bool] = None, 
                 log_level: Optional[str] = None) -> None:
    """Set up application logging configuration.
    
    Args:
        console_output: Override console output setting
        log_level: Override log level
    """
    # Get configuration
    config = Settings.LOGGING_CONFIG
    
    # Override settings if provided
    if console_output is None:
        console_output = config.get("console_output", True)
    if log_level is None:
        log_level = config.get("level", "INFO")
    
    # Ensure logs directory exists
    log_file = config["file"]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # Use colored formatter for console
        colored_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(colored_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=config.get("max_bytes", 10 * 1024 * 1024),  # 10MB default
            backupCount=config.get("backup_count", 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        # Fallback to basic file handler if rotation fails
        try:
            basic_file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
            basic_file_handler.setLevel(logging.DEBUG)
            basic_file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(basic_file_handler)
        except Exception as e2:
            # If file logging fails completely, just use console
            if console_output:
                print(f"Warning: Could not set up file logging: {e2}")
    
    # Error handler for critical issues
    error_log_file = log_file.parent / "errors.log"
    try:
        error_handler = logging.FileHandler(str(error_log_file), encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    except Exception:
        pass  # Error logging is optional
    
    # Log successful initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, Console: {console_output}")
    logger.debug(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """Change log level at runtime.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        numeric_level = getattr(logging, level.upper())
        logging.getLogger().setLevel(numeric_level)
        
        # Update console handlers
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(numeric_level)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Log level changed to {level.upper()}")
        
    except AttributeError:
        logger = logging.getLogger(__name__)
        logger.error(f"Invalid log level: {level}")


def add_handler(handler: logging.Handler) -> None:
    """Add a custom logging handler.
    
    Args:
        handler: Logging handler to add
    """
    try:
        logging.getLogger().addHandler(handler)
        logger = logging.getLogger(__name__)
        logger.debug(f"Added custom handler: {handler.__class__.__name__}")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to add handler: {e}")


def remove_handler(handler: logging.Handler) -> None:
    """Remove a logging handler.
    
    Args:
        handler: Logging handler to remove
    """
    try:
        logging.getLogger().removeHandler(handler)
        logger = logging.getLogger(__name__)
        logger.debug(f"Removed handler: {handler.__class__.__name__}")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to remove handler: {e}")


def log_exception(logger: logging.Logger, message: str = "An exception occurred") -> None:
    """Log exception with full traceback.
    
    Args:
        logger: Logger instance
        message: Optional message to include
    """
    logger.exception(message)


def get_log_file_path() -> Optional[Path]:
    """Get the path to the main log file.
    
    Returns:
        Optional[Path]: Path to log file or None if not configured
    """
    try:
        return Settings.LOGGING_CONFIG["file"]
    except Exception:
        return None


def get_log_stats() -> dict:
    """Get logging statistics and information.
    
    Returns:
        dict: Logging statistics
    """
    stats = {
        'handlers': [],
        'level': logging.getLogger().level,
        'level_name': logging.getLevelName(logging.getLogger().level)
    }
    
    try:
        # Get handler information
        for handler in logging.getLogger().handlers:
            handler_info = {
                'type': handler.__class__.__name__,
                'level': handler.level,
                'level_name': logging.getLevelName(handler.level)
            }
            
            # Add specific info for file handlers
            if isinstance(handler, logging.FileHandler):
                handler_info['file'] = getattr(handler, 'baseFilename', 'Unknown')
                
                # Add rotation info if available
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler_info['max_bytes'] = getattr(handler, 'maxBytes', 'Unknown')
                    handler_info['backup_count'] = getattr(handler, 'backupCount', 'Unknown')
            
            stats['handlers'].append(handler_info)
        
        # Get log file info if available
        log_file = get_log_file_path()
        if log_file and log_file.exists():
            stats['log_file'] = {
                'path': str(log_file),
                'size_bytes': log_file.stat().st_size,
                'size_mb': round(log_file.stat().st_size / (1024 * 1024), 2)
            }
    
    except Exception as e:
        stats['error'] = str(e)
    
    return stats


def cleanup_old_logs(max_age_days: int = 30) -> int:
    """Clean up old log files.
    
    Args:
        max_age_days: Maximum age in days for log files
        
    Returns:
        int: Number of files cleaned up
    """
    try:
        import time
        from pathlib import Path
        
        log_dir = Settings.LOGS_DIR
        if not log_dir.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        cleaned_count = 0
        
        # Find and remove old log files
        for log_file in log_dir.glob("*.log*"):
            try:
                file_age = current_time - log_file.stat().st_mtime
                if file_age > max_age_seconds:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not clean log file {log_file}: {e}")
        
        if cleaned_count > 0:
            logger = logging.getLogger(__name__)
            logger.info(f"Cleaned up {cleaned_count} old log files")
        
        return cleaned_count
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error cleaning up old logs: {e}")
        return 0


class LogContext:
    """Context manager for temporary log level changes."""
    
    def __init__(self, level: str):
        """Initialize log context.
        
        Args:
            level: Temporary log level
        """
        self.new_level = getattr(logging, level.upper())
        self.old_level = None
    
    def __enter__(self):
        """Enter context - change log level."""
        self.old_level = logging.getLogger().level
        logging.getLogger().setLevel(self.new_level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore log level."""
        if self.old_level is not None:
            logging.getLogger().setLevel(self.old_level)