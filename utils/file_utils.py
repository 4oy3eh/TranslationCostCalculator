"""
Translation Cost Calculator - File Utilities

Utility functions for file handling, validation, and manipulation.
"""

import hashlib
import logging
import mimetypes
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import tempfile
import os

from config.settings import Settings


class FileUtils:
    """Utility class for file operations."""
    
    def __init__(self):
        """Initialize file utilities."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def ensure_directory(directory_path: Path) -> bool:
        """Ensure directory exists, create if necessary.
        
        Args:
            directory_path: Path to directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size_readable(file_path: Path) -> str:
        """Get human-readable file size.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Human-readable size (e.g., "1.5 MB")
        """
        try:
            size_bytes = file_path.stat().st_size
        except (OSError, FileNotFoundError):
            return "0 B"
        
        # Size units
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
        """Calculate file hash for duplicate detection.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Optional[str]: File hash or None if error
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                chunk_size = 8192
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_file_mime_type(file_path: Path) -> str:
        """Get MIME type of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: MIME type or 'application/octet-stream' if unknown
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Check if filename is safe for filesystem operations.
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if filename is safe
        """
        # Check for empty or whitespace-only names
        if not filename or not filename.strip():
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check for reserved names on Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem operations.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '/', '\\']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Handle reserved names
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_part = Path(sanitized).stem.upper()
        if name_part in reserved_names:
            sanitized = f"file_{sanitized}"
        
        # Truncate if too long
        if len(sanitized) > 255:
            name = Path(sanitized).stem[:240]
            ext = Path(sanitized).suffix
            sanitized = f"{name}{ext}"
        
        # Ensure we have something
        if not sanitized:
            sanitized = "unnamed_file"
        
        return sanitized
    
    @staticmethod
    def copy_file_safely(source: Path, destination: Path, 
                        overwrite: bool = False) -> bool:
        """Copy file with safety checks.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if copy was successful
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Validate source
            if not source.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            if not source.is_file():
                logger.error(f"Source is not a file: {source}")
                return False
            
            # Check destination
            if destination.exists() and not overwrite:
                logger.error(f"Destination exists and overwrite=False: {destination}")
                return False
            
            # Ensure destination directory exists
            if not FileUtils.ensure_directory(destination.parent):
                return False
            
            # Copy file
            shutil.copy2(source, destination)
            logger.info(f"Successfully copied {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def create_backup_filename(original_path: Path) -> Path:
        """Create backup filename with timestamp.
        
        Args:
            original_path: Original file path
            
        Returns:
            Path: Backup file path
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = original_path.stem
        extension = original_path.suffix
        
        backup_name = f"{name}_backup_{timestamp}{extension}"
        return original_path.parent / backup_name
    
    @staticmethod
    def get_unique_filename(file_path: Path) -> Path:
        """Get unique filename by adding number if file exists.
        
        Args:
            file_path: Desired file path
            
        Returns:
            Path: Unique file path
        """
        if not file_path.exists():
            return file_path
        
        name = file_path.stem
        extension = file_path.suffix
        parent = file_path.parent
        counter = 1
        
        while True:
            new_name = f"{name}_{counter}{extension}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Safety break to avoid infinite loops
            if counter > 9999:
                # Use timestamp as fallback
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{name}_{timestamp}{extension}"
                return parent / new_name
    
    @staticmethod
    def validate_file_size(file_path: Path, max_size_mb: int = 50) -> Tuple[bool, str]:
        """Validate file size against maximum.
        
        Args:
            file_path: Path to validate
            max_size_mb: Maximum size in MB
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        try:
            if not file_path.exists():
                return False, "File does not exist"
            
            size_bytes = file_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > max_size_mb:
                readable_size = FileUtils.get_file_size_readable(file_path)
                return False, f"File size {readable_size} exceeds maximum {max_size_mb} MB"
            
            return True, f"File size OK: {FileUtils.get_file_size_readable(file_path)}"
            
        except Exception as e:
            return False, f"Error checking file size: {e}"
    
    @staticmethod
    def clean_temp_files(temp_dir: Path, max_age_hours: int = 24) -> int:
        """Clean old temporary files.
        
        Args:
            temp_dir: Temporary directory to clean
            max_age_hours: Maximum age in hours
            
        Returns:
            int: Number of files cleaned
        """
        logger = logging.getLogger(__name__)
        
        if not temp_dir.exists():
            return 0
        
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            file_path.unlink()
                            cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Error cleaning temp file {file_path}: {e}")
            
            logger.info(f"Cleaned {cleaned_count} temporary files from {temp_dir}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning temp directory {temp_dir}: {e}")
            return 0
    
    @staticmethod
    def get_file_info_detailed(file_path: Path) -> Dict[str, Any]:
        """Get detailed file information.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dict[str, Any]: Detailed file information
        """
    @staticmethod
    def get_file_info_detailed(file_path: Path) -> Dict[str, Any]:
        """Get detailed file information.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dict[str, Any]: Detailed file information
        """
        info = {
            'name': file_path.name,
            'stem': file_path.stem,
            'suffix': file_path.suffix,
            'path': str(file_path),
            'exists': file_path.exists()
        }
        
        if file_path.exists():
            try:
                stat = file_path.stat()
                info.update({
                    'size_bytes': stat.st_size,
                    'size_readable': FileUtils.get_file_size_readable(file_path),
                    'modified_time': stat.st_mtime,
                    'is_file': file_path.is_file(),
                    'is_directory': file_path.is_dir(),
                    'mime_type': FileUtils.get_file_mime_type(file_path),
                    'file_hash': FileUtils.calculate_file_hash(file_path),
                    'safe_filename': FileUtils.is_safe_filename(file_path.name)
                })
            except Exception as e:
                info['error'] = str(e)
        
        return info


class TempFileManager:
    """Manages temporary files for the application."""
    
    def __init__(self):
        """Initialize temp file manager."""
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "translation_calculator"
        FileUtils.ensure_directory(self.temp_dir)
    
    def create_temp_file(self, suffix: str = "", prefix: str = "calc_") -> Path:
        """Create a temporary file.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path: Path to created temporary file
        """
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix, 
                prefix=prefix, 
                dir=self.temp_dir
            )
            os.close(fd)  # Close file descriptor
            
            temp_file = Path(temp_path)
            self.logger.debug(f"Created temporary file: {temp_file}")
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Error creating temporary file: {e}")
            # Fallback to simple temp file
            return self.temp_dir / f"{prefix}{os.getpid()}{suffix}"
    
    def create_temp_dir(self, prefix: str = "calc_dir_") -> Path:
        """Create a temporary directory.
        
        Args:
            prefix: Directory prefix
            
        Returns:
            Path: Path to created temporary directory
        """
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
            self.logger.debug(f"Created temporary directory: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            self.logger.error(f"Error creating temporary directory: {e}")
            # Fallback
            fallback_dir = self.temp_dir / f"{prefix}{os.getpid()}"
            FileUtils.ensure_directory(fallback_dir)
            return fallback_dir
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            int: Number of files cleaned
        """
        return FileUtils.clean_temp_files(self.temp_dir, max_age_hours)
    
    def get_temp_file_for_upload(self, original_filename: str) -> Path:
        """Get temporary file path for uploaded file.
        
        Args:
            original_filename: Original filename
            
        Returns:
            Path: Temporary file path
        """
        # Sanitize filename
        safe_name = FileUtils.sanitize_filename(original_filename)
        
        # Create unique temp file
        temp_file = self.temp_dir / safe_name
        return FileUtils.get_unique_filename(temp_file)


# Global temp file manager instance
_temp_manager = None


def get_temp_manager() -> TempFileManager:
    """Get global temporary file manager.
    
    Returns:
        TempFileManager: Global temp manager instance
    """
    global _temp_manager
    if _temp_manager is None:
        _temp_manager = TempFileManager()
    return _temp_manager


def ensure_data_directories() -> bool:
    """Ensure all required data directories exist.
    
    Returns:
        bool: True if all directories exist or were created
    """
    directories = [
        Settings.DATA_DIR,
        Settings.LOGS_DIR,
        Settings.ASSETS_DIR,
        Settings.MIGRATIONS_DIR.parent,  # database directory
    ]
    
    success = True
    for directory in directories:
        if not FileUtils.ensure_directory(directory):
            success = False
    
    return success
            