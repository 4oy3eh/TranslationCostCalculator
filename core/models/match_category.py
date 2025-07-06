"""
Translation Cost Calculator - Match Category Models

Defines match category types and their mappings for different CAT tools.
Supports Trados CSV, Phrase JSON, and Excel format variations.
"""

from enum import Enum
from typing import Dict, Optional


class MatchCategoryType(Enum):
    """Translation match category types with display names and mapping support."""
    
    CONTEXT_MATCH = "Context Match"
    REPETITIONS = "Repetitions"
    EXACT_MATCH = "100%"
    HIGH_FUZZY = "95% - 99%"
    MEDIUM_HIGH_FUZZY = "85% - 94%"
    MEDIUM_FUZZY = "75% - 84%"
    LOW_FUZZY = "50% - 74%"
    NO_MATCH = "No Match"
    MT_MATCH = "MT Match"
    
    def __str__(self) -> str:
        """Return display name for the match category."""
        return self.value
    
    @classmethod
    def get_all_categories(cls) -> list['MatchCategoryType']:
        """Get all match categories in display order.
        
        Returns:
            list[MatchCategoryType]: All categories in logical order
        """
        return [
            cls.CONTEXT_MATCH,
            cls.REPETITIONS,
            cls.EXACT_MATCH,
            cls.HIGH_FUZZY,
            cls.MEDIUM_HIGH_FUZZY,
            cls.MEDIUM_FUZZY,
            cls.LOW_FUZZY,
            cls.NO_MATCH,
            cls.MT_MATCH
        ]
    
    @classmethod
    def get_standard_categories(cls) -> list['MatchCategoryType']:
        """Get standard CAT analysis categories (excluding MT).
        
        Returns:
            list[MatchCategoryType]: Standard categories without MT
        """
        return [
            cls.CONTEXT_MATCH,
            cls.REPETITIONS,
            cls.EXACT_MATCH,
            cls.HIGH_FUZZY,
            cls.MEDIUM_HIGH_FUZZY,
            cls.MEDIUM_FUZZY,
            cls.LOW_FUZZY,
            cls.NO_MATCH
        ]
    
    @classmethod
    def from_phrase_key(cls, phrase_key: str) -> 'MatchCategoryType':
        """Map Phrase JSON keys to match categories.
        
        Args:
            phrase_key: Key from Phrase JSON format
            
        Returns:
            MatchCategoryType: Corresponding match category
        """
        phrase_mapping = {
            'contextMatch': cls.CONTEXT_MATCH,
            'repetitions': cls.REPETITIONS,
            'match100': cls.EXACT_MATCH,
            'match95': cls.HIGH_FUZZY,
            'match85': cls.MEDIUM_HIGH_FUZZY,
            'match75': cls.MEDIUM_FUZZY,
            'match50': cls.LOW_FUZZY,
            'match0': cls.NO_MATCH
        }
        return phrase_mapping.get(phrase_key, cls.NO_MATCH)
    
    @classmethod
    def from_trados_header(cls, header: str) -> Optional['MatchCategoryType']:
        """Map Trados CSV headers to match categories.
        
        Args:
            header: Header text from Trados CSV
            
        Returns:
            Optional[MatchCategoryType]: Corresponding match category or None
        """
        # Normalize header text
        normalized = header.strip()
        
        trados_mapping = {
            'Context Match': cls.CONTEXT_MATCH,
            'Repetitions': cls.REPETITIONS,
            '100%': cls.EXACT_MATCH,
            '95% - 99%': cls.HIGH_FUZZY,
            '85% - 94%': cls.MEDIUM_HIGH_FUZZY,
            '75% - 84%': cls.MEDIUM_FUZZY,
            '50% - 74%': cls.LOW_FUZZY,
            'No Match': cls.NO_MATCH
        }
        return trados_mapping.get(normalized)
    
    @classmethod
    def from_display_name(cls, display_name: str) -> Optional['MatchCategoryType']:
        """Get match category from display name.
        
        Args:
            display_name: Display name string
            
        Returns:
            Optional[MatchCategoryType]: Matching category or None
        """
        for category in cls:
            if category.value == display_name:
                return category
        return None
    
    def get_default_rate(self) -> float:
        """Get default rate for this match category.
        
        Returns:
            float: Default rate per word in EUR
        """
        from config.settings import Settings
        return Settings.DEFAULT_RATES.get(self.value, 0.12)
    
    def is_fuzzy_match(self) -> bool:
        """Check if this is a fuzzy match category.
        
        Returns:
            bool: True if fuzzy match category
        """
        return self in [
            self.HIGH_FUZZY,
            self.MEDIUM_HIGH_FUZZY, 
            self.MEDIUM_FUZZY,
            self.LOW_FUZZY
        ]
    
    def is_exact_match(self) -> bool:
        """Check if this is an exact match category.
        
        Returns:
            bool: True if exact match category
        """
        return self in [
            self.CONTEXT_MATCH,
            self.REPETITIONS,
            self.EXACT_MATCH
        ]
    
    def supports_mt_breakdown(self) -> bool:
        """Check if this category supports MT/TM breakdown.
        
        Returns:
            bool: True if category supports MT breakdown
        """
        return self == self.EXACT_MATCH


class MatchCategoryMapping:
    """Utility class for mapping between different CAT tool formats."""
    
    @staticmethod
    def get_phrase_to_display_mapping() -> Dict[str, str]:
        """Get mapping from Phrase JSON keys to display names.
        
        Returns:
            Dict[str, str]: Mapping dictionary
        """
        return {
            'contextMatch': MatchCategoryType.CONTEXT_MATCH.value,
            'repetitions': MatchCategoryType.REPETITIONS.value,
            'match100': MatchCategoryType.EXACT_MATCH.value,
            'match95': MatchCategoryType.HIGH_FUZZY.value,
            'match85': MatchCategoryType.MEDIUM_HIGH_FUZZY.value,
            'match75': MatchCategoryType.MEDIUM_FUZZY.value,
            'match50': MatchCategoryType.LOW_FUZZY.value,
            'match0': MatchCategoryType.NO_MATCH.value
        }
    
    @staticmethod
    def get_trados_columns_for_category() -> Dict[str, list[str]]:
        """Get expected column names for each category in Trados CSV.
        
        Returns:
            Dict[str, list[str]]: Category to column names mapping
        """
        base_columns = ["Segments", "Words", "Placeables", "Percent"]
        with_characters = base_columns + ["Characters"]
        
        return {
            'base_columns': base_columns,
            'with_characters': with_characters,
            'categories': [cat.value for cat in MatchCategoryType.get_standard_categories()]
        }
    
    @staticmethod
    def detect_trados_format_variant(header_line: str) -> str:
        """Detect Trados CSV format variant based on semicolon count.
        
        Args:
            header_line: First header line from CSV
            
        Returns:
            str: Format variant ('with_characters' or 'without_characters')
        """
        semicolon_count = header_line.count(';')
        
        # Count semicolons between categories
        # 8 categories * 5 semicolons = 40 (with characters)
        # 8 categories * 4 semicolons = 32 (without characters)
        if semicolon_count >= 35:  # Allow some tolerance
            return 'with_characters'
        else:
            return 'without_characters'
    
    @staticmethod
    def get_excel_header_patterns() -> list[str]:
        """Get common Excel header patterns for auto-detection.
        
        Returns:
            list[str]: List of header patterns to search for
        """
        return [
            "segments", "words", "characters", "percent", "percentage",
            "context", "repetition", "match", "fuzzy", "no match",
            "100%", "95%", "85%", "75%", "50%"
        ]