"""
Translation Cost Calculator - Project Domain Model

Project entity representing a translation project with associated files,
translator, client, and calculation settings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from core.models.analysis import ProjectAnalysisData


@dataclass
class Project:
    """Translation project domain model."""
    
    # Core identification
    id: Optional[int] = None
    name: str = ""
    
    # Project relationships
    translator_id: Optional[int] = None
    client_id: Optional[int] = None
    language_pair_id: Optional[int] = None
    
    # Language information
    source_language: str = ""
    target_language: str = ""
    
    # Project settings
    mt_percentage: int = 70  # Default MT percentage for 100% matches
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Analysis data (not persisted directly)
    analysis_data: Optional[ProjectAnalysisData] = field(default=None, compare=False)
    
    def __post_init__(self):
        """Initialize default values and validate data."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Validate MT percentage
        self.mt_percentage = max(0, min(100, self.mt_percentage))
        
        # Initialize analysis data if name is provided
        if self.name and self.analysis_data is None:
            self.analysis_data = ProjectAnalysisData(project_name=self.name)
    
    def get_language_pair_code(self) -> str:
        """Get language pair in standard format.
        
        Returns:
            str: Language pair as "source>target"
        """
        return f"{self.source_language}>{self.target_language}"
    
    def get_display_name(self) -> str:
        """Get project display name with language pair.
        
        Returns:
            str: Display name including language information
        """
        if self.source_language and self.target_language:
            return f"{self.name} ({self.get_language_pair_code()})"
        return self.name
    
    def is_valid(self) -> bool:
        """Check if project has all required fields.
        
        Returns:
            bool: True if project is valid
        """
        return (
            bool(self.name.strip()) and
            bool(self.source_language) and
            bool(self.target_language) and
            self.translator_id is not None
        )
    
    def has_analysis_data(self) -> bool:
        """Check if project has analysis data.
        
        Returns:
            bool: True if analysis data is available
        """
        return (
            self.analysis_data is not None and
            self.analysis_data.get_file_count() > 0
        )
    
    def get_total_words(self) -> int:
        """Get total word count for the project.
        
        Returns:
            int: Total word count across all files
        """
        if not self.has_analysis_data():
            return 0
        return self.analysis_data.get_total_words()
    
    def get_file_count(self) -> int:
        """Get number of files in the project.
        
        Returns:
            int: Number of analysis files
        """
        if not self.has_analysis_data():
            return 0
        return self.analysis_data.get_file_count()
    
    def calculate_total_cost(self, rates: dict, minimum_fee: Optional[Decimal] = None) -> Decimal:
        """Calculate total project cost including minimum fee.
        
        Args:
            rates: Dictionary of rates by match category
            minimum_fee: Optional minimum fee to apply
            
        Returns:
            Decimal: Total project cost
        """
        if not self.has_analysis_data():
            return Decimal('0.00')
        
        # Calculate base cost from analysis
        base_cost = self.analysis_data.calculate_total_cost(rates, self.mt_percentage)
        
        # Apply minimum fee if specified
        if minimum_fee is not None and minimum_fee > base_cost:
            return minimum_fee.quantize(Decimal('0.01'))
        
        return base_cost
    
    def get_cost_breakdown(self, rates: dict) -> dict:
        """Get detailed cost breakdown for the project.
        
        Args:
            rates: Dictionary of rates by match category
            
        Returns:
            dict: Detailed cost breakdown
        """
        if not self.has_analysis_data():
            return {}
        
        breakdown = {
            'project_info': {
                'name': self.name,
                'language_pair': self.get_language_pair_code(),
                'total_words': self.get_total_words(),
                'file_count': self.get_file_count(),
                'mt_percentage': self.mt_percentage
            },
            'files': [],
            'aggregated': {},
            'total_cost': 0.0
        }
        
        # Add file-level breakdowns
        for file_data in self.analysis_data.files:
            file_breakdown = file_data.get_cost_breakdown(rates, self.mt_percentage)
            file_cost = float(file_data.calculate_total_cost(rates, self.mt_percentage))
            
            breakdown['files'].append({
                'filename': file_data.filename,
                'categories': file_breakdown,
                'total_cost': file_cost,
                'total_words': file_data.get_total_words()
            })
        
        # Add aggregated breakdown
        aggregated_categories = self.analysis_data.get_aggregated_categories()
        for category, data in aggregated_categories.items():
            if data.words > 0:
                rate = rates.get(category, Decimal('0.00'))
                word_breakdown = data.get_cost_calculation_words(self.mt_percentage)
                
                if category.supports_mt_breakdown() and word_breakdown['mt'] > 0:
                    from core.models.match_category import MatchCategoryType
                    tm_rate = rate
                    mt_rate = rates.get(MatchCategoryType.MT_MATCH, rate)
                    
                    tm_cost = Decimal(str(word_breakdown['tm'])) * tm_rate
                    mt_cost = Decimal(str(word_breakdown['mt'])) * mt_rate
                    total_cost = tm_cost + mt_cost
                    
                    breakdown['aggregated'][category.value] = {
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
                    breakdown['aggregated'][category.value] = {
                        'words': data.words,
                        'rate': float(rate),
                        'cost': float(cost),
                        'segments': data.segments,
                        'percent': data.percent
                    }
        
        # Calculate total cost
        breakdown['total_cost'] = float(self.calculate_total_cost(rates))
        
        return breakdown
    
    def update_analysis_data(self, analysis_data: ProjectAnalysisData) -> None:
        """Update project with new analysis data.
        
        Args:
            analysis_data: New analysis data to set
        """
        self.analysis_data = analysis_data
        self.updated_at = datetime.now()
    
    def clear_analysis_data(self) -> None:
        """Clear all analysis data from the project."""
        self.analysis_data = ProjectAnalysisData(project_name=self.name)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert project to dictionary for serialization.
        
        Returns:
            dict: Project data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'translator_id': self.translator_id,
            'client_id': self.client_id,
            'language_pair_id': self.language_pair_id,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'mt_percentage': self.mt_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_words': self.get_total_words(),
            'file_count': self.get_file_count()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Create project from dictionary data.
        
        Args:
            data: Dictionary containing project data
            
        Returns:
            Project: New project instance
        """
        project = cls()
        project.id = data.get('id')
        project.name = data.get('name', '')
        project.translator_id = data.get('translator_id')
        project.client_id = data.get('client_id')
        project.language_pair_id = data.get('language_pair_id')
        project.source_language = data.get('source_language', '')
        project.target_language = data.get('target_language', '')
        project.mt_percentage = data.get('mt_percentage', 70)
        
        # Parse datetime fields
        if data.get('created_at'):
            project.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            project.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return project
    
    def __str__(self) -> str:
        """String representation of the project."""
        return self.get_display_name()
    
    def __repr__(self) -> str:
        """Developer representation of the project."""
        return (f"Project(id={self.id}, name='{self.name}', "
                f"language_pair='{self.get_language_pair_code()}', "
                f"words={self.get_total_words()})")


@dataclass
class ProjectFile:
    """Represents a file within a project for database storage."""
    
    id: Optional[int] = None
    project_id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    parsed_data: str = ""  # JSON serialized FileAnalysisData
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_valid(self) -> bool:
        """Check if project file has required fields.
        
        Returns:
            bool: True if file data is valid
        """
        return (
            bool(self.filename.strip()) and
            bool(self.file_path.strip()) and
            bool(self.parsed_data.strip()) and
            self.project_id is not None
        )
    
    def to_dict(self) -> dict:
        """Convert project file to dictionary.
        
        Returns:
            dict: File data as dictionary
        """
        return {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'parsed_data': self.parsed_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectFile':
        """Create project file from dictionary.
        
        Args:
            data: Dictionary containing file data
            
        Returns:
            ProjectFile: New file instance
        """
        file_obj = cls()
        file_obj.id = data.get('id')
        file_obj.project_id = data.get('project_id')
        file_obj.filename = data.get('filename', '')
        file_obj.file_path = data.get('file_path', '')
        file_obj.parsed_data = data.get('parsed_data', '')
        
        if data.get('created_at'):
            file_obj.created_at = datetime.fromisoformat(data['created_at'])
        
        return file_obj