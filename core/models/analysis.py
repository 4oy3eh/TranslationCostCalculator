"""
Translation Cost Calculator - File Analysis Models

Data models for CAT analysis results with support for TM/MT breakdown
and multi-file projects. Handles data from Trados CSV, Phrase JSON, and Excel formats.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from decimal import Decimal

from core.models.match_category import MatchCategoryType


@dataclass
class MatchCategoryData:
    """Data for a single match category within a file analysis."""
    
    category: MatchCategoryType
    segments: int = 0
    words: int = 0
    characters: int = 0
    placeables: int = 0
    percent: float = 0.0
    
    # TM/MT breakdown for 100% matches (Phrase JSON support)
    tm_words: Optional[int] = None
    mt_words: Optional[int] = None
    nt_words: Optional[int] = None  # New translation words
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Ensure non-negative values
        self.segments = max(0, self.segments)
        self.words = max(0, self.words)
        self.characters = max(0, self.characters)
        self.placeables = max(0, self.placeables)
        self.percent = max(0.0, min(100.0, self.percent))
        
        # Validate TM/MT breakdown if present
        if self.has_tm_mt_breakdown():
            self._validate_tm_mt_breakdown()
    
    def has_tm_mt_breakdown(self) -> bool:
        """Check if this category has TM/MT breakdown data.
        
        Returns:
            bool: True if TM/MT breakdown is available
        """
        return (self.tm_words is not None or 
                self.mt_words is not None or 
                self.nt_words is not None)
    
    def _validate_tm_mt_breakdown(self) -> None:
        """Validate TM/MT breakdown consistency."""
        if not self.category.supports_mt_breakdown():
            # Clear TM/MT data for categories that don't support it
            self.tm_words = None
            self.mt_words = None
            self.nt_words = None
            return
        
        # Ensure all breakdown values are non-negative
        if self.tm_words is not None:
            self.tm_words = max(0, self.tm_words)
        if self.mt_words is not None:
            self.mt_words = max(0, self.mt_words)
        if self.nt_words is not None:
            self.nt_words = max(0, self.nt_words)
    
    def get_tm_words(self, mt_percentage: int = 70) -> int:
        """Get TM words for cost calculation.
        
        Args:
            mt_percentage: Percentage of 100% matches that are MT
            
        Returns:
            int: Number of TM words
        """
        if self.has_tm_mt_breakdown() and self.tm_words is not None:
            return self.tm_words
        
        # Calculate based on MT percentage for 100% matches
        if self.category.supports_mt_breakdown():
            tm_percentage = 100 - mt_percentage
            return int(self.words * tm_percentage / 100)
        
        # Non-100% matches are all TM
        return self.words
    
    def get_mt_words(self, mt_percentage: int = 70) -> int:
        """Get MT words for cost calculation.
        
        Args:
            mt_percentage: Percentage of 100% matches that are MT
            
        Returns:
            int: Number of MT words
        """
        if self.has_tm_mt_breakdown() and self.mt_words is not None:
            return self.mt_words
        
        # Calculate based on MT percentage for 100% matches only
        if self.category.supports_mt_breakdown():
            return int(self.words * mt_percentage / 100)
        
        # Non-100% matches have no MT
        return 0
    
    def get_cost_calculation_words(self, mt_percentage: int = 70) -> Dict[str, int]:
        """Get word breakdown for cost calculation.
        
        Args:
            mt_percentage: Percentage of 100% matches that are MT
            
        Returns:
            Dict[str, int]: Word breakdown with 'tm' and 'mt' keys
        """
        return {
            'tm': self.get_tm_words(mt_percentage),
            'mt': self.get_mt_words(mt_percentage),
            'total': self.words
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchCategoryData':
        """Create MatchCategoryData from dictionary.
        
        Args:
            data: Dictionary containing match category data
            
        Returns:
            MatchCategoryData: New instance
        """
        # Get category from name
        category = MatchCategoryType.from_display_name(data.get('category', ''))
        if not category:
            category = MatchCategoryType.NO_MATCH
        
        return cls(
            category=category,
            segments=data.get('segments', 0),
            words=data.get('words', 0),
            characters=data.get('characters', 0),
            placeables=data.get('placeables', 0),
            percent=data.get('percent', 0.0),
            tm_words=data.get('tm_words'),
            mt_words=data.get('mt_words'),
            nt_words=data.get('nt_words')
        )
    
    def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary for serialization.
            
            Returns:
                Dict[str, Any]: Dictionary representation
            """
            return {
                'filename': self.filename,
                'source_language': self.source_language,
                'target_language': self.target_language,
                'file_path': self.file_path,
                'analysis_date': self.analysis_date,
                'cat_tool': self.cat_tool,
                'total_words': self.get_total_words(),
                'total_segments': self.get_total_segments(),
                'language_pair': self.get_language_pair_code(),
                'categories': {
                    category.value: data.to_dict() 
                    for category, data in self.categories.items()
                    if hasattr(data, 'to_dict') and hasattr(category, 'value')
                }
            }


@dataclass
class FileAnalysisData:
    """Complete analysis data for a single file."""
    
    filename: str
    source_language: str
    target_language: str
    categories: Dict[MatchCategoryType, MatchCategoryData] = field(default_factory=dict)
    
    # File metadata
    file_path: Optional[str] = None
    analysis_date: Optional[str] = None
    cat_tool: Optional[str] = None  # "Trados", "Phrase", "Excel", etc.
    
    def __post_init__(self):
        """Initialize with empty categories if none provided."""
        if not self.categories:
            self.categories = {
                category: MatchCategoryData(category=category)
                for category in MatchCategoryType.get_standard_categories()
            }
    
    def get_category_data(self, category: MatchCategoryType) -> MatchCategoryData:
        """Get data for a specific match category.
        
        Args:
            category: Match category to retrieve
            
        Returns:
            MatchCategoryData: Category data (empty if not found)
        """
        return self.categories.get(category, MatchCategoryData(category=category))
    
    def set_category_data(self, category: MatchCategoryType, data: MatchCategoryData) -> None:
        """Set data for a specific match category.
        
        Args:
            category: Match category to set
            data: Category data to store
        """
        data.category = category  # Ensure consistency
        self.categories[category] = data
    
    def get_total_words(self) -> int:
        """Get total word count across all categories.
        
        Returns:
            int: Total word count
        """
        return sum(data.words for data in self.categories.values())
    
    def get_total_segments(self) -> int:
        """Get total segment count across all categories.
        
        Returns:
            int: Total segment count
        """
        return sum(data.segments for data in self.categories.values())
    
    def get_language_pair_code(self) -> str:
        """Get language pair in standard format.
        
        Returns:
            str: Language pair as "source>target"
        """
        return f"{self.source_language}>{self.target_language}"
    
    def calculate_total_cost(self, rates: Dict[MatchCategoryType, Decimal], 
                           mt_percentage: int = 70) -> Decimal:
        """Calculate total cost for this file analysis.
        
        Args:
            rates: Rate per word for each category
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Decimal: Total cost
        """
        total_cost = Decimal('0.00')
        
        for category, data in self.categories.items():
            if category not in rates:
                continue
            
            # Get word breakdown for cost calculation
            word_breakdown = data.get_cost_calculation_words(mt_percentage)
            
            # Calculate cost based on TM/MT breakdown
            if category.supports_mt_breakdown() and word_breakdown['mt'] > 0:
                # Use MT rate for MT words, TM rate for TM words
                tm_rate = rates[category]
                mt_rate = rates.get(MatchCategoryType.MT_MATCH, tm_rate)
                
                tm_cost = Decimal(str(word_breakdown['tm'])) * tm_rate
                mt_cost = Decimal(str(word_breakdown['mt'])) * mt_rate
                category_cost = tm_cost + mt_cost
            else:
                # Standard calculation
                category_cost = Decimal(str(data.words)) * rates[category]
            
            total_cost += category_cost
        
        return total_cost.quantize(Decimal('0.01'))
    
    def get_cost_breakdown(self, rates: Dict[MatchCategoryType, Decimal],
                          mt_percentage: int = 70) -> Dict[str, Dict[str, any]]:
        """Get detailed cost breakdown by category.
        
        Args:
            rates: Rate per word for each category
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Dict: Detailed cost breakdown
        """
        breakdown = {}
        
        for category, data in self.categories.items():
            if data.words == 0:
                continue
            
            word_breakdown = data.get_cost_calculation_words(mt_percentage)
            rate = rates.get(category, Decimal('0.00'))
            
            if category.supports_mt_breakdown() and word_breakdown['mt'] > 0:
                tm_rate = rate
                mt_rate = rates.get(MatchCategoryType.MT_MATCH, rate)
                
                tm_cost = Decimal(str(word_breakdown['tm'])) * tm_rate
                mt_cost = Decimal(str(word_breakdown['mt'])) * mt_rate
                total_cost = tm_cost + mt_cost
                
                breakdown[category.value] = {
                    'total_words': data.words,
                    'tm_words': word_breakdown['tm'],
                    'mt_words': word_breakdown['mt'],
                    'tm_rate': float(tm_rate),
                    'mt_rate': float(mt_rate),
                    'tm_cost': float(tm_cost),
                    'mt_cost': float(mt_cost),
                    'total_cost': float(total_cost),
                    'segments': data.segments,
                    'percent': data.percent
                }
            else:
                cost = Decimal(str(data.words)) * rate
                breakdown[category.value] = {
                    'words': data.words,
                    'rate': float(rate),
                    'cost': float(cost),
                    'segments': data.segments,
                    'percent': data.percent
                }
        
        return breakdown
    
    def is_valid(self) -> bool:
        """Check if analysis data is valid.
        
        Returns:
            bool: True if data is valid
        """
        return (
            bool(self.filename) and
            bool(self.source_language) and
            bool(self.target_language) and
            self.get_total_words() > 0
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileAnalysisData':
        """Create FileAnalysisData from dictionary.
        
        Args:
            data: Dictionary containing file analysis data
            
        Returns:
            FileAnalysisData: New instance
        """
        file_analysis = cls(
            filename=data.get('filename', ''),
            source_language=data.get('source_language', ''),
            target_language=data.get('target_language', ''),
            file_path=data.get('file_path'),
            analysis_date=data.get('analysis_date'),
            cat_tool=data.get('cat_tool')
        )
        
        # Deserialize categories
        categories_data = data.get('categories', {})
        for category_name, category_data in categories_data.items():
            category_type = MatchCategoryType.from_display_name(category_name)
            if category_type:
                category_obj = MatchCategoryData.from_dict(category_data)
                file_analysis.categories[category_type] = category_obj
        
        return file_analysis
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            'filename': self.filename,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'file_path': self.file_path,
            'analysis_date': self.analysis_date,
            'cat_tool': self.cat_tool,
            'categories': {
                category.value: data.to_dict() 
                for category, data in self.categories.items()
            }
        }


@dataclass
class ProjectAnalysisData:
    """Complete analysis data for a project with multiple files."""
    
    project_name: str
    files: List[FileAnalysisData] = field(default_factory=list)
    
    def add_file_analysis(self, file_analysis: FileAnalysisData) -> None:
        """Add file analysis to the project.
        
        Args:
            file_analysis: File analysis data to add
        """
        self.files.append(file_analysis)
    
    def get_file_count(self) -> int:
        """Get number of files in the project.
        
        Returns:
            int: Number of files
        """
        return len(self.files)
    
    def get_total_words(self) -> int:
        """Get total word count across all files.
        
        Returns:
            int: Total word count
        """
        return sum(file_data.get_total_words() for file_data in self.files)
    
    def get_aggregated_categories(self) -> Dict[MatchCategoryType, MatchCategoryData]:
        """Get aggregated category data across all files.
        
        Returns:
            Dict[MatchCategoryType, MatchCategoryData]: Aggregated data
        """
        aggregated = {}
        
        for category in MatchCategoryType.get_standard_categories():
            total_segments = 0
            total_words = 0
            total_characters = 0
            total_placeables = 0
            total_tm_words = 0
            total_mt_words = 0
            total_nt_words = 0
            has_breakdown = False
            
            for file_data in self.files:
                cat_data = file_data.get_category_data(category)
                total_segments += cat_data.segments
                total_words += cat_data.words
                total_characters += cat_data.characters
                total_placeables += cat_data.placeables
                
                if cat_data.has_tm_mt_breakdown():
                    has_breakdown = True
                    total_tm_words += cat_data.tm_words or 0
                    total_mt_words += cat_data.mt_words or 0
                    total_nt_words += cat_data.nt_words or 0
            
            # Calculate percentage
            project_total_words = self.get_total_words()
            percent = (total_words / project_total_words * 100) if project_total_words > 0 else 0.0
            
            aggregated_data = MatchCategoryData(
                category=category,
                segments=total_segments,
                words=total_words,
                characters=total_characters,
                placeables=total_placeables,
                percent=percent
            )
            
            # Add TM/MT breakdown if available
            if has_breakdown:
                aggregated_data.tm_words = total_tm_words
                aggregated_data.mt_words = total_mt_words
                aggregated_data.nt_words = total_nt_words
            
            aggregated[category] = aggregated_data
        
        return aggregated
    
    def calculate_total_cost(self, rates: Dict[MatchCategoryType, Decimal],
                           mt_percentage: int = 70) -> Decimal:
        """Calculate total project cost.
        
        Args:
            rates: Rate per word for each category
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Decimal: Total project cost
        """
        total_cost = Decimal('0.00')
        for file_data in self.files:
            total_cost += file_data.calculate_total_cost(rates, mt_percentage)
        
        return total_cost.quantize(Decimal('0.01'))