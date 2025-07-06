"""
Translation Cost Calculator - Parsers Package

File parsing layer for CAT analysis files with support for multiple formats.
Implements intelligent format detection and extensible parser architecture.
"""

from .base_parser import BaseParser, ParserError
from .column_detector import TradosColumnDetector, ColumnMapping
from .trados_csv_parser import TradosCSVParser
from .parser_factory import ParserFactory, get_parser_factory, parse_file, can_parse_file, get_supported_extensions

__all__ = [
    'BaseParser', 'ParserError',
    'TradosColumnDetector', 'ColumnMapping', 
    'TradosCSVParser',
    'ParserFactory', 'get_parser_factory', 'parse_file', 'can_parse_file', 'get_supported_extensions'
]