"""
Translation Cost Calculator - Fixed Column Detection System

Intelligent column detection for Trados CSV files with support for both
format variations (with and without Characters columns).
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.models.match_category import MatchCategoryType


@dataclass
class ColumnMapping:
    """Represents the column mapping for a Trados CSV file."""
    
    format_type: str  # 'with_characters' or 'without_characters'
    categories: Dict[MatchCategoryType, Dict[str, int]]  # category -> {field: column_index}
    fixed_columns: Dict[str, int]  # fixed column names -> column_index
    total_columns: Dict[str, int]  # total section columns -> column_index
    
    def get_category_column(self, category: MatchCategoryType, field: str) -> Optional[int]:
        """Get column index for a category field.
        
        Args:
            category: Match category
            field: Field name ('segments', 'words', 'characters', 'placeables', 'percent')
            
        Returns:
            Optional[int]: Column index or None if not found
        """
        if category in self.categories:
            return self.categories[category].get(field)
        return None
    
    def has_characters_column(self) -> bool:
        """Check if this format includes characters columns.
        
        Returns:
            bool: True if format includes characters
        """
        return self.format_type == 'with_characters'


class TradosColumnDetector:
    """Detects and maps columns in Trados CSV files."""
    
    def __init__(self):
        """Initialize the column detector."""
        self.logger = logging.getLogger(__name__)
    
    def detect_format(self, header_lines: List[str]) -> str:
        """Detect Trados CSV format based on header structure.
        
        Args:
            header_lines: Header lines from CSV (should be at least 2 lines)
            
        Returns:
            str: Format type ('with_characters' or 'without_characters')
        """
        if len(header_lines) < 2:
            self.logger.warning("Insufficient header lines for format detection")
            return 'without_characters'
        
        # Check the second header line for "Characters" columns
        second_line = header_lines[1]
        column_headers = [col.strip() for col in second_line.split(';')]
        
        # Count "Characters" occurrences (should be one per category if format includes characters)
        characters_count = sum(1 for header in column_headers if 'Characters' in header)
        
        # Count total columns - this is the most reliable indicator
        total_columns = len(column_headers)
        
        # Also check semicolon count as backup
        semicolon_count = second_line.count(';')
        
        self.logger.debug(f"Column headers count: {len(column_headers)}")
        self.logger.debug(f"Characters columns found: {characters_count}")
        self.logger.debug(f"Semicolon count in header: {semicolon_count}")
        self.logger.debug(f"Total columns: {total_columns}")
        
        # FIXED LOGIC: Use total column count as primary indicator
        # Format with characters typically has 45+ columns
        # Format without characters typically has 35-40 columns
        if total_columns >= 45 or characters_count >= 6:
            format_type = 'with_characters'
            self.logger.info(f"Detected Trados CSV format: WITH Characters columns ({total_columns} cols)")
        else:
            format_type = 'without_characters'
            self.logger.info(f"Detected Trados CSV format: WITHOUT Characters columns ({total_columns} cols)")
        
        return format_type
    
    def extract_categories_from_header(self, header_line: str) -> List[str]:
        """Extract category names from header line.
        
        Args:
            header_line: First header line containing category names
            
        Returns:
            List[str]: List of category names in order
        """
        categories = []
        
        # Split on multiple semicolons to find category blocks
        parts = header_line.split(';;;')
        
        for part in parts:
            if part.strip():
                # Extract category name (remove extra semicolons)
                category_name = part.replace(';', '').strip()
                if category_name and category_name not in ['Total', 'File']:
                    categories.append(category_name)
        
        self.logger.debug(f"Extracted categories: {categories}")
        return categories
    
    def map_columns(self, header_lines: List[str]) -> ColumnMapping:
        """Create complete column mapping from header lines.
        
        Args:
            header_lines: List of header lines (typically 2 lines)
            
        Returns:
            ColumnMapping: Complete column mapping
        """
        if len(header_lines) < 2:
            raise ValueError("Trados CSV requires at least 2 header lines")
        
        # Detect format from header structure
        format_type = self.detect_format(header_lines)
        
        # Extract categories from first header line
        category_names = self.extract_categories_from_header(header_lines[0])
        
        # Parse column headers from second line
        column_headers = [col.strip() for col in header_lines[1].split(';')]
        
        # Create mapping
        mapping = self._create_column_mapping(
            format_type, category_names, column_headers
        )
        
        self.logger.info(f"Created column mapping for {len(category_names)} categories")
        return mapping
    
    def _create_column_mapping(self, format_type: str, category_names: List[str], 
                              column_headers: List[str]) -> ColumnMapping:
        """Create detailed column mapping.
        
        Args:
            format_type: Format type ('with_characters' or 'without_characters')
            category_names: List of category names
            column_headers: List of column header names
            
        Returns:
            ColumnMapping: Detailed column mapping
        """
        categories = {}
        fixed_columns = {}
        total_columns = {}
        
        # Define expected column patterns based on format
        if format_type == 'with_characters':
            # Format: Segments, Words, Characters, Placeables, Percent
            category_fields = ['segments', 'words', 'characters', 'placeables', 'percent']
            fields_per_category = 5
        else:
            # Format: Segments, Words, Placeables, Percent (no Characters)
            category_fields = ['segments', 'words', 'placeables', 'percent']
            fields_per_category = 4
        
        self.logger.info(f"Using format '{format_type}' with {fields_per_category} fields per category")
        
        # Map fixed columns (File, Tagging Errors, Chars/Word)
        # These are always in the first few columns
        for i, header in enumerate(column_headers[:5]):  # Check first 5 columns
            header_lower = header.lower()
            if 'file' in header_lower:
                fixed_columns['File'] = i
            elif 'tagging' in header_lower and 'error' in header_lower:
                fixed_columns['Tagging Errors'] = i
            elif 'chars' in header_lower and 'word' in header_lower:
                fixed_columns['Chars/Word'] = i
        
        # Ensure we have File column
        if 'File' not in fixed_columns:
            # Default to first column if not found
            fixed_columns['File'] = 0
            self.logger.warning("File column not found in headers, defaulting to column 0")
        
        # Map category columns starting after fixed columns
        col_index = 3  # Start after fixed columns (File, Tagging Errors, Chars/Word)
        
        for category_name in category_names:
            # Try to map category name to MatchCategoryType
            category_type = self._map_category_name_to_type(category_name)
            
            if category_type:
                category_mapping = {}
                
                # Map each field for this category
                for field_idx, field in enumerate(category_fields):
                    if col_index < len(column_headers):
                        category_mapping[field] = col_index
                        col_index += 1
                    else:
                        self.logger.warning(f"Not enough columns for {category_name}.{field}")
                
                categories[category_type] = category_mapping
                
                self.logger.debug(f"Mapped {category_name} -> {category_mapping}")
            else:
                # Skip unknown categories but advance column index
                self.logger.warning(f"Unknown category: {category_name}, skipping {fields_per_category} columns")
                col_index += fields_per_category
        
        # Map total columns (usually at the end)
        # Look for total section based on remaining columns
        remaining_cols = len(column_headers) - col_index
        if remaining_cols >= 3:  # At least Segments, Words, something
            total_columns['segments'] = col_index
            total_columns['words'] = col_index + 1
            
            if format_type == 'with_characters':
                if remaining_cols >= 4:
                    total_columns['placeables'] = col_index + 2
                    total_columns['characters'] = col_index + 3
            else:
                # Without characters format
                if remaining_cols >= 3:
                    total_columns['placeables'] = col_index + 2
                if remaining_cols >= 4:
                    total_columns['characters'] = col_index + 3  # May exist at the end
        
        self.logger.debug(f"Fixed columns: {fixed_columns}")
        self.logger.debug(f"Category mappings: {len(categories)} categories")
        self.logger.debug(f"Total columns: {total_columns}")
        
        return ColumnMapping(
            format_type=format_type,
            categories=categories,
            fixed_columns=fixed_columns,
            total_columns=total_columns
        )
    
    def _map_category_name_to_type(self, category_name: str) -> Optional[MatchCategoryType]:
        """Map category name to MatchCategoryType.
        
        Args:
            category_name: Category name from header
            
        Returns:
            Optional[MatchCategoryType]: Mapped category type or None
        """
        # Direct mapping for standard Trados categories
        mapping = {
            'Context Match': MatchCategoryType.CONTEXT_MATCH,
            'Repetitions': MatchCategoryType.REPETITIONS,
            '100%': MatchCategoryType.EXACT_MATCH,
            '95% - 99%': MatchCategoryType.HIGH_FUZZY,
            '85% - 94%': MatchCategoryType.MEDIUM_HIGH_FUZZY,
            '75% - 84%': MatchCategoryType.MEDIUM_FUZZY,
            '50% - 74%': MatchCategoryType.LOW_FUZZY,
            'No Match': MatchCategoryType.NO_MATCH
        }
        
        return mapping.get(category_name)
    
    def validate_mapping(self, mapping: ColumnMapping, total_columns: int) -> bool:
        """Validate that the column mapping is reasonable.
        
        Args:
            mapping: Column mapping to validate
            total_columns: Total number of columns in the CSV
            
        Returns:
            bool: True if mapping appears valid
        """
        try:
            # Check that we have basic required mappings
            if 'File' not in mapping.fixed_columns:
                self.logger.error("Missing File column mapping")
                return False
            
            # Check that we have some category mappings
            if not mapping.categories:
                self.logger.error("No category mappings found")
                return False
            
            # Check that column indices are within bounds
            all_indices = []
            
            # Collect all mapped indices
            all_indices.extend(mapping.fixed_columns.values())
            all_indices.extend(mapping.total_columns.values())
            
            for category_mapping in mapping.categories.values():
                all_indices.extend(category_mapping.values())
            
            # Check bounds
            for index in all_indices:
                if index < 0 or index >= total_columns:
                    self.logger.error(f"Column index {index} out of bounds (0-{total_columns-1})")
                    return False
            
            self.logger.info("Column mapping validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating column mapping: {e}")
            return False
    
    def get_mapping_summary(self, mapping: ColumnMapping) -> Dict[str, any]:
        """Get a summary of the column mapping.
        
        Args:
            mapping: Column mapping to summarize
            
        Returns:
            Dict: Mapping summary
        """
        return {
            'format_type': mapping.format_type,
            'has_characters': mapping.has_characters_column(),
            'category_count': len(mapping.categories),
            'categories': [cat.value for cat in mapping.categories.keys()],
            'fixed_columns': list(mapping.fixed_columns.keys()),
            'total_columns': list(mapping.total_columns.keys())
        }