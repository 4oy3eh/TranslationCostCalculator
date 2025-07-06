"""
Translation Cost Calculator - Base Parser Interface

Abstract base parser defining the interface for all CAT analysis file parsers.
Provides common functionality and ensures consistent behavior across all parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from core.models.analysis import FileAnalysisData


class BaseParser(ABC):
    """Abstract base parser for CAT analysis files."""
    
    def __init__(self):
        """Initialize the parser."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List[str]: Supported file extensions (e.g., ['.csv', '.json'])
        """
        pass
    
    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Get parser name for identification.
        
        Returns:
            str: Parser name (e.g., 'Trados CSV', 'Phrase JSON')
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if this parser can handle the file
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: Path) -> Optional[FileAnalysisData]:
        """Parse the CAT analysis file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Optional[FileAnalysisData]: Parsed analysis data or None if failed
        """
        pass
    
    def validate_file_exists(self, file_path: Path) -> bool:
        """Validate that file exists and is readable.
        
        Args:
            file_path: Path to validate
            
        Returns:
            bool: True if file exists and is readable
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            if not file_path.is_file():
                self.logger.error(f"Path is not a file: {file_path}")
                return False
            
            # Try to read the file to check permissions
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Read just one character
            
            return True
            
        except PermissionError:
            self.logger.error(f"No permission to read file: {file_path}")
            return False
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    f.read(1)
                return True
            except UnicodeDecodeError:
                self.logger.error(f"File encoding not supported: {file_path}")
                return False
        except Exception as e:
            self.logger.error(f"Error validating file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file information.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dict[str, Any]: File information
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size_bytes': stat.st_size,
                'extension': file_path.suffix.lower(),
                'modified_time': stat.st_mtime,
                'path': str(file_path)
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                'name': file_path.name,
                'size_bytes': 0,
                'extension': file_path.suffix.lower(),
                'modified_time': 0,
                'path': str(file_path)
            }
    
    def detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            str: Detected encoding (defaults to 'utf-8')
        """
        # Try common encodings in order of preference
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Try to read the entire file
                    f.read()
                self.logger.debug(f"Detected encoding {encoding} for {file_path}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                self.logger.warning(f"Error testing encoding {encoding}: {e}")
                continue
        
        # Default to utf-8 if nothing else works
        self.logger.warning(f"Could not detect encoding for {file_path}, using utf-8")
        return 'utf-8'
    
    def parse_language_pair_from_filename(self, filename: str) -> tuple[str, str]:
        """Extract language pair from filename patterns.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            tuple[str, str]: (source_language, target_language) or ('', '') if not found
        """
        # Common patterns for language pairs in filenames
        patterns = [
            ' | ',  # Trados format: "file | en>de"
            '_',    # "file_en_de" or "file_en-de"
            '-',    # "file-en-de"
            ' '     # "file en de"
        ]
        
        for pattern in patterns:
            if pattern in filename:
                parts = filename.split(pattern)
                if len(parts) >= 2:
                    # Look for language pair pattern
                    lang_part = parts[-1]  # Usually at the end
                    
                    # Check for > separator (Trados style)
                    if '>' in lang_part:
                        langs = lang_part.split('>')
                        if len(langs) == 2:
                            source = langs[0].strip().lower()
                            target = langs[1].strip().lower()
                            
                            # Basic validation - language codes are usually 2-5 chars
                            if 2 <= len(source) <= 5 and 2 <= len(target) <= 5:
                                return source, target
        
        self.logger.warning(f"Could not extract language pair from filename: {filename}")
        return '', ''
    
    def log_parsing_start(self, file_path: Path) -> None:
        """Log the start of parsing process.
        
        Args:
            file_path: File being parsed
        """
        file_info = self.get_file_info(file_path)
        self.logger.info(
            f"Starting {self.parser_name} parsing: {file_path.name} "
            f"({file_info['size_bytes']} bytes)"
        )
    
    def log_parsing_result(self, file_path: Path, success: bool, 
                          analysis_data: Optional[FileAnalysisData] = None) -> None:
        """Log the result of parsing process.
        
        Args:
            file_path: File that was parsed
            success: Whether parsing was successful
            analysis_data: Resulting analysis data if successful
        """
        if success and analysis_data:
            self.logger.info(
                f"Successfully parsed {file_path.name}: "
                f"{analysis_data.get_total_words()} words, "
                f"{analysis_data.get_total_segments()} segments"
            )
        else:
            self.logger.error(f"Failed to parse {file_path.name}")


class ParserError(Exception):
    """Custom exception for parser errors."""
    
    def __init__(self, message: str, parser_name: str = "", file_path: str = ""):
        """Initialize parser error.
        
        Args:
            message: Error message
            parser_name: Name of parser that failed
            file_path: Path of file that failed to parse
        """
        self.message = message
        self.parser_name = parser_name
        self.file_path = file_path
        
        full_message = message
        if parser_name:
            full_message = f"[{parser_name}] {full_message}"
        if file_path:
            full_message = f"{full_message} (File: {file_path})"
        
        super().__init__(full_message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        return self.message