"""
Translation Cost Calculator - Parser Factory

Factory for creating appropriate parsers based on file type and content.
Phase 1 version supporting Trados CSV with extensibility for future parsers.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from parsers.base_parser import BaseParser
from parsers.trados_csv_parser import TradosCSVParser
from core.models.analysis import FileAnalysisData


class ParserFactory:
    """Factory for creating file parsers."""
    
    def __init__(self):
        """Initialize the parser factory."""
        self.logger = logging.getLogger(__name__)
        self._parsers = {}
        self._register_parsers()
    
    def _register_parsers(self) -> None:
        """Register all available parsers."""
        # Phase 1: Trados CSV parser
        self._parsers['trados_csv'] = TradosCSVParser()
        
        # Phase 3: Additional parsers will be added here
        # self._parsers['phrase_json'] = PhraseJSONParser()
        # self._parsers['excel'] = ExcelParser()
        
        self.logger.info(f"Registered {len(self._parsers)} parsers: {list(self._parsers.keys())}")
    
    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for the given file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Optional[BaseParser]: Appropriate parser or None if no parser found
        """
        if not file_path.exists():
            self.logger.error(f"File does not exist: {file_path}")
            return None
        
        # Try each parser to see which can handle the file
        for parser_name, parser in self._parsers.items():
            try:
                if parser.can_parse(file_path):
                    self.logger.info(f"Selected {parser_name} parser for {file_path.name}")
                    return parser
            except Exception as e:
                self.logger.warning(f"Error checking {parser_name} for {file_path}: {e}")
                continue
        
        self.logger.error(f"No suitable parser found for {file_path.name}")
        return None
    
    def parse_file(self, file_path: Path) -> Optional[FileAnalysisData]:
        """Parse file using appropriate parser.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Optional[FileAnalysisData]: Parsed analysis data or None if failed
        """
        parser = self.get_parser(file_path)
        if not parser:
            return None
        
        try:
            return parser.parse(file_path)
        except Exception as e:
            self.logger.error(f"Error parsing {file_path} with {parser.parser_name}: {e}")
            return None
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions.
        
        Returns:
            List[str]: List of supported extensions
        """
        extensions = set()
        for parser in self._parsers.values():
            extensions.update(parser.supported_extensions)
        
        return sorted(list(extensions))
    
    def get_parser_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered parsers.
        
        Returns:
            Dict[str, Dict[str, Any]]: Parser information
        """
        info = {}
        for name, parser in self._parsers.items():
            info[name] = {
                'name': parser.parser_name,
                'extensions': parser.supported_extensions,
                'class': parser.__class__.__name__
            }
        
        return info
    
    def can_parse_file(self, file_path: Path) -> bool:
        """Check if any parser can handle the file.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file can be parsed
        """
        return self.get_parser(file_path) is not None
    
    def get_file_analysis_summary(self, file_path: Path) -> Dict[str, Any]:
        """Get summary of what could be parsed from file.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dict[str, Any]: Analysis summary
        """
        base_info = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'extension': file_path.suffix.lower(),
            'can_parse': False
        }
        
        parser = self.get_parser(file_path)
        if not parser:
            base_info['reason'] = 'No suitable parser found'
            return base_info
        
        base_info['can_parse'] = True
        base_info['parser_name'] = parser.parser_name
        
        # Get parser-specific summary if available
        if hasattr(parser, 'get_parsing_summary'):
            try:
                parser_summary = parser.get_parsing_summary(file_path)
                base_info.update(parser_summary)
            except Exception as e:
                self.logger.warning(f"Error getting parser summary: {e}")
                base_info['summary_error'] = str(e)
        
        return base_info
    
    def validate_file_for_parsing(self, file_path: Path) -> Dict[str, Any]:
        """Validate file and provide detailed feedback.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'valid': False,
            'issues': [],
            'warnings': [],
            'parser': None
        }
        
        # Basic file checks
        if not file_path.exists():
            validation['issues'].append('File does not exist')
            return validation
        
        if not file_path.is_file():
            validation['issues'].append('Path is not a file')
            return validation
        
        if file_path.stat().st_size == 0:
            validation['issues'].append('File is empty')
            return validation
        
        # Extension check
        extension = file_path.suffix.lower()
        supported_extensions = self.get_supported_extensions()
        
        if extension not in supported_extensions:
            validation['warnings'].append(
                f'Extension {extension} not in supported list: {supported_extensions}'
            )
        
        # Parser check
        parser = self.get_parser(file_path)
        if not parser:
            validation['issues'].append('No parser can handle this file')
            return validation
        
        validation['valid'] = True
        validation['parser'] = parser.parser_name
        
        # Size warnings
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10:
            validation['warnings'].append(f'Large file size: {file_size_mb:.1f} MB')
        
        return validation


# Global factory instance
_parser_factory = None


def get_parser_factory() -> ParserFactory:
    """Get the global parser factory instance.
    
    Returns:
        ParserFactory: Global factory instance
    """
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
    return _parser_factory


def parse_file(file_path: Path) -> Optional[FileAnalysisData]:
    """Convenience function to parse a file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        Optional[FileAnalysisData]: Parsed analysis data or None if failed
    """
    return get_parser_factory().parse_file(file_path)


def can_parse_file(file_path: Path) -> bool:
    """Convenience function to check if file can be parsed.
    
    Args:
        file_path: Path to check
        
    Returns:
        bool: True if file can be parsed
    """
    return get_parser_factory().can_parse_file(file_path)


def get_supported_extensions() -> List[str]:
    """Convenience function to get supported extensions.
    
    Returns:
        List[str]: Supported file extensions
    """
    return get_parser_factory().get_supported_extensions()