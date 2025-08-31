"""
Logging utility for Butler Connect
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any


def setup_logging(logging_config: Dict[str, Any]) -> None:
    """Setup logging configuration"""
    
    # Default configuration
    level = logging_config.get('level', 'INFO')
    log_file = logging_config.get('file_path', 'logs/butler_connect.log')
    max_file_size = logging_config.get('max_file_size', '10MB')
    backup_count = logging_config.get('backup_count', 5)
    
    # Ensure logs directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert max_file_size to bytes
    size_multipliers = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    max_bytes = 10 * 1024 * 1024  # Default 10MB
    
    if isinstance(max_file_size, str):
        for suffix, multiplier in size_multipliers.items():
            if max_file_size.upper().endswith(suffix):
                size_value = float(max_file_size[:-2])
                max_bytes = int(size_value * multiplier)
                break
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
