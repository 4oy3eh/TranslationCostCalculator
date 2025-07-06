"""
Translation Cost Calculator - Trados CSV Parser

Complete parser for Trados CSV analysis files with support for both
format variations (with and without Characters columns).
"""

import csv
from pathlib import Path
from typing import Optional, List, Dict, Any
import re

from parsers.base_parser import BaseParser, ParserError
from parsers.column_detector import TradosColumnDetector, ColumnMapping
from core.models.analysis import FileAnalysisData, MatchCategoryData
from core.models.match_category import MatchCategoryType
from config.settings import Settings


class TradosCSVParser(BaseParser):
    """Parser for Trados CSV analysis files."""
    
    def __init__(self):
        """Initialize the Trados CSV parser."""
        super().__init__()
        self.column_detector = TradosColumnDetector()
    
    @property
    def supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.csv']
    
    @property
    def parser_name(self) -> str:
        """Get parser name."""
        return "Trados CSV"
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if this is a Trados CSV file
        """
        if not self.validate_file_exists(file_path):
            return False
        
        if file_path.suffix.lower() != '.csv':
            return False
        
        try:
            # Read first few lines to check for Trados CSV pattern
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first two lines
                first_line = f.readline().strip()
                second_line = f.readline().strip() if f.tell() < file_path.stat().st_size else ""
            
            # Check for Trados CSV patterns
            return self._is_trados_csv_format(first_line, second_line)
            
        except Exception as e:
            self.logger.error(f"Error checking Trados CSV format: {e}")
            return False
    
    def parse(self, file_path: Path) -> Optional[FileAnalysisData]:
        """Parse the Trados CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Optional[FileAnalysisData]: Parsed analysis data or None if failed
        """
        self.log_parsing_start(file_path)
        
        try:
            # Detect encoding
            encoding = self.detect_encoding(file_path)
            
            # Read and parse the CSV
            with open(file_path, 'r', encoding=encoding) as f:
                # Read all lines
                lines = [line.strip() for line in f.readlines()]
            
            if len(lines) < 3:  # Need at least headers + 1 data row
                raise ParserError(
                    "CSV file must have at least 3 lines (2 headers + data)",
                    self.parser_name, str(file_path)
                )
            
            # Parse headers and create column mapping
            header_lines = lines[:2]
            column_mapping = self.column_detector.map_columns(header_lines)
            
            # Parse data rows
            data_rows = lines[2:]
            analysis_data = self._parse_data_rows(
                data_rows, column_mapping, file_path
            )
            
            if analysis_data:
                analysis_data.cat_tool = "Trados"
                analysis_data.file_path = str(file_path)
                
                self.log_parsing_result(file_path, True, analysis_data)
                return analysis_data
            else:
                self.log_parsing_result(file_path, False)
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing Trados CSV {file_path}: {e}")
            self.log_parsing_result(file_path, False)
            return None
    
    def _is_trados_csv_format(self, first_line: str, second_line: str) -> bool:
        """Check if the lines indicate a Trados CSV format.
        
        Args:
            first_line: First line of the file
            second_line: Second line of the file
            
        Returns:
            bool: True if this appears to be a Trados CSV
        """
        # Check for characteristic Trados CSV patterns
        trados_indicators = [
            # Category names that are typical for Trados
            'Context Match', 'Repetitions', '100%', '95% - 99%',
            'No Match', 'Total'
        ]
        
        # Check first line for category pattern
        has_categories = any(indicator in first_line for indicator in trados_indicators)
        
        # Check for semicolon delimiter (Trados uses semicolons)
        has_semicolons = ';' in first_line and ';' in second_line
        
        # Check for column headers pattern in second line
        typical_headers = ['File', 'Segments', 'Words', 'Percent']
        has_headers = any(header in second_line for header in typical_headers)
        
        # Check for multiple semicolons pattern (category separators)
        has_category_separators = ';;;' in first_line
        
        is_trados = (
            has_categories and 
            has_semicolons and 
            has_headers and 
            has_category_separators
        )
        
        self.logger.debug(f"Trados format detection: {is_trados}")
        self.logger.debug(f"  Categories: {has_categories}")
        self.logger.debug(f"  Semicolons: {has_semicolons}")
        self.logger.debug(f"  Headers: {has_headers}")
        self.logger.debug(f"  Separators: {has_category_separators}")
        
        return is_trados
    
    def _parse_data_rows(self, data_rows: List[str], column_mapping: ColumnMapping,
                        file_path: Path) -> Optional[FileAnalysisData]:
        """Parse data rows into FileAnalysisData.
        
        Args:
            data_rows: List of data row strings
            column_mapping: Column mapping for the file
            file_path: Original file path
            
        Returns:
            Optional[FileAnalysisData]: Parsed analysis data
        """
        if not data_rows:
            self.logger.error("No data rows to parse")
            return None
        
        # For Trados CSV, we typically take the first data row for single file analysis
        # or aggregate multiple rows for multi-file analysis
        
        # Parse first row to get primary analysis data
        first_row = data_rows[0]
        row_data = [col.strip(' "') for col in first_row.split(';')]
        
        # Validate column count
        if not self.column_detector.validate_mapping(column_mapping, len(row_data)):
            self.logger.error("Column mapping validation failed")
            return None
        
        # Extract file information
        file_info = self._extract_file_info(row_data, column_mapping)
        
        # Create FileAnalysisData
        analysis_data = FileAnalysisData(
            filename=file_info['filename'],
            source_language=file_info['source_language'],
            target_language=file_info['target_language']
        )
        
        # Parse category data
        for category_type, category_mapping in column_mapping.categories.items():
            category_data = self._parse_category_data(
                row_data, category_mapping, column_mapping.has_characters_column()
            )
            analysis_data.set_category_data(category_type, category_data)
        
        # Validate the parsed data
        if not analysis_data.is_valid():
            self.logger.error("Parsed analysis data is not valid")
            return None
        
        self.logger.info(
            f"Parsed {analysis_data.filename}: "
            f"{analysis_data.get_total_words()} words, "
            f"{analysis_data.get_total_segments()} segments"
        )
        
        return analysis_data
    
    def _extract_file_info(self, row_data: List[str], 
                          column_mapping: ColumnMapping) -> Dict[str, str]:
        """Extract file information from row data.
        
        Args:
            row_data: Parsed row data
            column_mapping: Column mapping
            
        Returns:
            Dict[str, str]: File information
        """
        file_col_index = column_mapping.fixed_columns.get('File', 0)
        
        if file_col_index < len(row_data):
            file_cell = row_data[file_col_index].strip(' "')
        else:
            file_cell = "unknown_file"
        
    def _extract_file_info(self, row_data: List[str], 
                          column_mapping: ColumnMapping) -> Dict[str, str]:
        """Extract file information from row data.
        
        Args:
            row_data: Parsed row data
            column_mapping: Column mapping
            
        Returns:
            Dict[str, str]: File information
        """
        file_col_index = column_mapping.fixed_columns.get('File', 0)
        
        if file_col_index < len(row_data):
            file_cell = row_data[file_col_index].strip(' "')
        else:
            file_cell = "unknown_file"
        
        # Parse Trados format: "filename | source_lang>target_lang"
        filename = file_cell
        source_language = ""
        target_language = ""
        
        if ' | ' in file_cell:
            parts = file_cell.split(' | ')
            filename = parts[0].strip()
            
            if len(parts) > 1 and '>' in parts[1]:
                lang_pair = parts[1].strip()
                lang_parts = lang_pair.split('>')
                if len(lang_parts) == 2:
                    source_language = lang_parts[0].strip()
                    target_language = lang_parts[1].strip()
        
        # If language extraction failed, try filename parsing
        if not source_language or not target_language:
            fallback_source, fallback_target = self.parse_language_pair_from_filename(filename)
            if fallback_source and fallback_target:
                source_language = fallback_source
                target_language = fallback_target
        
        return {
            'filename': filename,
            'source_language': source_language,
            'target_language': target_language
        }
    
    def _parse_category_data(self, row_data: List[str], category_mapping: Dict[str, int],
                           has_characters: bool) -> MatchCategoryData:
        """Parse category data from row.
        
        Args:
            row_data: Parsed row data
            category_mapping: Column indices for this category
            has_characters: Whether format includes characters column
            
        Returns:
            MatchCategoryData: Parsed category data
        """
        # Extract values with safe conversion
        segments = self._safe_int_conversion(
            row_data, category_mapping.get('segments', -1)
        )
        words = self._safe_int_conversion(
            row_data, category_mapping.get('words', -1)
        )
        placeables = self._safe_int_conversion(
            row_data, category_mapping.get('placeables', -1)
        )
        percent = self._safe_float_conversion(
            row_data, category_mapping.get('percent', -1)
        )
        
        # Characters column is optional
        characters = 0
        if has_characters:
            characters = self._safe_int_conversion(
                row_data, category_mapping.get('characters', -1)
            )
        
        # Create MatchCategoryData (category will be set by caller)
        return MatchCategoryData(
            category=MatchCategoryType.NO_MATCH,  # Will be overridden
            segments=segments,
            words=words,
            characters=characters,
            placeables=placeables,
            percent=percent
        )
    
    def _safe_int_conversion(self, row_data: List[str], col_index: int) -> int:
        """Safely convert column value to integer.
        
        Args:
            row_data: Row data
            col_index: Column index
            
        Returns:
            int: Converted value or 0 if conversion fails
        """
        if col_index < 0 or col_index >= len(row_data):
            return 0
        
        try:
            value = row_data[col_index].strip()
            if not value:
                return 0
            
            # Handle decimal values by truncating
            if '.' in value:
                return int(float(value))
            else:
                return int(value)
                
        except (ValueError, TypeError):
            self.logger.warning(f"Could not convert '{row_data[col_index]}' to int")
            return 0
    
    def _safe_float_conversion(self, row_data: List[str], col_index: int) -> float:
        """Safely convert column value to float.
        
        Args:
            row_data: Row data
            col_index: Column index
            
        Returns:
            float: Converted value or 0.0 if conversion fails
        """
        if col_index < 0 or col_index >= len(row_data):
            return 0.0
        
        try:
            value = row_data[col_index].strip()
            if not value:
                return 0.0
            
            return float(value)
            
        except (ValueError, TypeError):
            self.logger.warning(f"Could not convert '{row_data[col_index]}' to float")
            return 0.0
    
    def parse_multiple_files(self, file_path: Path) -> Optional[List[FileAnalysisData]]:
        """Parse CSV with multiple file entries.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Optional[List[FileAnalysisData]]: List of analysis data for each file
        """
        self.log_parsing_start(file_path)
        
        try:
            encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                lines = [line.strip() for line in f.readlines()]
            
            if len(lines) < 3:
                raise ParserError(
                    "CSV file must have at least 3 lines",
                    self.parser_name, str(file_path)
                )
            
            # Parse headers
            header_lines = lines[:2]
            column_mapping = self.column_detector.map_columns(header_lines)
            
            # Parse each data row as separate file
            file_analyses = []
            data_rows = lines[2:]
            
            for i, row in enumerate(data_rows):
                try:
                    row_data = [col.strip(' "') for col in row.split(';')]
                    
                    if len(row_data) < 3:  # Skip empty or malformed rows
                        continue
                    
                    # Extract file info
                    file_info = self._extract_file_info(row_data, column_mapping)
                    
                    # Create analysis data
                    analysis_data = FileAnalysisData(
                        filename=file_info['filename'],
                        source_language=file_info['source_language'],
                        target_language=file_info['target_language']
                    )
                    analysis_data.cat_tool = "Trados"
                    analysis_data.file_path = str(file_path)
                    
                    # Parse categories
                    for category_type, category_mapping_dict in column_mapping.categories.items():
                        category_data = self._parse_category_data(
                            row_data, category_mapping_dict, column_mapping.has_characters_column()
                        )
                        category_data.category = category_type
                        analysis_data.set_category_data(category_type, category_data)
                    
                    if analysis_data.is_valid():
                        file_analyses.append(analysis_data)
                    else:
                        self.logger.warning(f"Invalid analysis data for row {i+1}")
                        
                except Exception as e:
                    self.logger.error(f"Error parsing row {i+1}: {e}")
                    continue
            
            if file_analyses:
                self.logger.info(f"Parsed {len(file_analyses)} files from {file_path.name}")
                return file_analyses
            else:
                self.logger.error("No valid file analyses found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing multiple files from {file_path}: {e}")
            return None
    
    def get_parsing_summary(self, file_path: Path) -> Dict[str, Any]:
        """Get a summary of what would be parsed without full parsing.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dict[str, Any]: Parsing summary
        """
        try:
            if not self.can_parse(file_path):
                return {'can_parse': False, 'reason': 'Not a valid Trados CSV file'}
            
            encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                lines = [line.strip() for line in f.readlines()[:10]]  # Read first 10 lines
            
            if len(lines) < 2:
                return {'can_parse': False, 'reason': 'Insufficient header lines'}
            
            # Analyze headers
            header_lines = lines[:2]
            column_mapping = self.column_detector.map_columns(header_lines)
            mapping_summary = self.column_detector.get_mapping_summary(column_mapping)
            
            # Count data rows
            data_row_count = len(lines) - 2
            
            return {
                'can_parse': True,
                'parser_name': self.parser_name,
                'format_type': mapping_summary['format_type'],
                'has_characters': mapping_summary['has_characters'],
                'category_count': mapping_summary['category_count'],
                'categories': mapping_summary['categories'],
                'estimated_files': data_row_count,
                'encoding': encoding,
                'file_size': file_path.stat().st_size
            }
            
        except Exception as e:
            return {
                'can_parse': False,
                'reason': f'Error analyzing file: {e}'
            }