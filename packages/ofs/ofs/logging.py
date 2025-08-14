"""Centralized logging system for OFS.

This module provides standardized logging functionality across all OFS modules,
replacing scattered print statements with proper logging infrastructure.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Setup standardized logger for OFS modules.
    
    Creates a logger with consistent formatting and output handling.
    Loggers are cached to avoid duplicate handlers.
    
    Args:
        name: Logger name (typically module name)
        level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
        
    Examples:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Operation completed successfully")
        
        >>> logger = setup_logger(__name__, "DEBUG")
        >>> logger.debug("Detailed debugging information")
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter with timestamp, module name, level, and message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Set default level
        logger.setLevel(logging.INFO)
    
    # Override level if specified
    if level:
        try:
            logger.setLevel(getattr(logging, level.upper()))
        except AttributeError:
            logger.warning(f"Invalid log level '{level}', using INFO")
            logger.setLevel(logging.INFO)
    
    return logger


def setup_file_logger(name: str, log_file: Path, level: Optional[str] = None) -> logging.Logger:
    """Setup file-based logger for OFS operations.
    
    Creates a logger that writes to both console and file.
    Useful for long-running operations or debugging.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Optional log level
        
    Returns:
        Configured logger with file and console handlers
    """
    logger = logging.getLogger(f"{name}.file")
    
    if not logger.handlers:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Set level
        logger.setLevel(logging.INFO)
    
    if level:
        try:
            logger.setLevel(getattr(logging, level.upper()))
        except AttributeError:
            logger.warning(f"Invalid log level '{level}', using INFO")
    
    return logger


class OFSLoggerMixin:
    """Mixin class to add logging capabilities to OFS classes.
    
    Provides a standardized way to add logging to any OFS class.
    The logger name is automatically derived from the class name.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = setup_logger(f"ofs.{self.__class__.__name__.lower()}")
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger for this instance."""
        return self._logger


def log_operation(operation_name: str):
    """Decorator to log function entry and exit with timing.
    
    Args:
        operation_name: Human-readable name for the operation
        
    Returns:
        Decorator function
        
    Examples:
        @log_operation("Loading project index")
        def load_project_index(project_path):
            # Implementation here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = setup_logger(func.__module__)
            start_time = datetime.now()
            
            logger.info(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed {operation_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed {operation_name} after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator


def log_performance(threshold_seconds: float = 1.0):
    """Decorator to log performance warnings for slow operations.
    
    Args:
        threshold_seconds: Time threshold above which to log a warning
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = setup_logger(func.__module__)
            start_time = datetime.now()
            
            result = func(*args, **kwargs)
            
            duration = (datetime.now() - start_time).total_seconds()
            if duration > threshold_seconds:
                logger.warning(
                    f"Slow operation: {func.__name__} took {duration:.2f}s "
                    f"(threshold: {threshold_seconds}s)"
                )
            
            return result
        return wrapper
    return decorator


# Module-level logger for this logging module
_module_logger = setup_logger(__name__)


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name.
    
    Convenience function that wraps setup_logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return setup_logger(name)


def set_global_log_level(level: str) -> None:
    """Set log level for all OFS loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        log_level = getattr(logging, level.upper())
        
        # Set level for all existing OFS loggers
        for logger_name in logging.Logger.manager.loggerDict:
            if logger_name.startswith('ofs.'):
                logger = logging.getLogger(logger_name)
                logger.setLevel(log_level)
        
        _module_logger.info(f"Set global OFS log level to {level.upper()}")
        
    except AttributeError:
        _module_logger.error(f"Invalid log level '{level}'")
        raise ValueError(f"Invalid log level '{level}'")


def configure_logging_from_config(config: Dict[str, Any]) -> None:
    """Configure logging from OFS configuration.
    
    Args:
        config: OFS configuration dictionary
    """
    log_config = config.get('logging', {})
    
    # Set global level if specified
    if 'level' in log_config:
        set_global_log_level(log_config['level'])
    
    # Configure file logging if specified
    if 'file' in log_config:
        log_file = Path(log_config['file'])
        file_logger = setup_file_logger('ofs.main', log_file, log_config.get('level'))
        file_logger.info("File logging configured")
    
    _module_logger.info("Logging configuration applied")