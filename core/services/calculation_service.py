"""
Translation Cost Calculator - Calculation Service

Core business logic for cost calculation with MT percentage handling,
rate hierarchy resolution, and project cost aggregation.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.models.analysis import FileAnalysisData, ProjectAnalysisData
from core.models.match_category import MatchCategoryType
from core.models.project import Project
from core.models.rate import Rate, RateCalculator
from core.models.translator import Translator, Client
from core.repositories.rate_repository import RateRepository, LanguagePairRepository, MatchCategoryRepository
from config.database import DatabaseManager


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a calculation."""
    
    # Category-level costs
    category_costs: Dict[str, Dict[str, Any]]
    
    # Summary totals
    subtotal: Decimal
    minimum_fee: Decimal
    total_cost: Decimal
    minimum_fee_applied: bool
    
    # Additional metadata
    total_words: int
    total_segments: int
    mt_percentage: int
    currency: str = "EUR"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'category_costs': self.category_costs,
            'subtotal': float(self.subtotal),
            'minimum_fee': float(self.minimum_fee),
            'total_cost': float(self.total_cost),
            'minimum_fee_applied': self.minimum_fee_applied,
            'total_words': self.total_words,
            'total_segments': self.total_segments,
            'mt_percentage': self.mt_percentage,
            'currency': self.currency
        }


class CalculationService:
    """Service for performing cost calculations with business logic."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize calculation service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.rate_repository = RateRepository(db_manager)
        self.language_pair_repository = LanguagePairRepository(db_manager)
        self.match_category_repository = MatchCategoryRepository(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def calculate_file_cost(self, file_analysis: FileAnalysisData, 
                           translator_id: int, client_id: Optional[int] = None,
                           mt_percentage: int = 70) -> Optional[CostBreakdown]:
        """Calculate cost for a single file analysis.
        
        Args:
            file_analysis: File analysis data
            translator_id: Translator ID
            client_id: Optional client ID for client-specific rates
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Optional[CostBreakdown]: Cost breakdown or None if calculation failed
        """
        try:
            # Get language pair ID
            language_pair = self.language_pair_repository.get_or_create(
                file_analysis.source_language, file_analysis.target_language
            )
            
            if not language_pair:
                self.logger.error(f"Could not resolve language pair: {file_analysis.get_language_pair_code()}")
                return None
            
            # Get rates for all categories
            rates = self._get_rates_for_calculation(
                translator_id, language_pair.id, client_id
            )
            
            if not rates:
                self.logger.error("No rates found for calculation")
                return None
            
            # Calculate cost breakdown
            return self._calculate_breakdown(
                file_analysis, rates, mt_percentage, client_id
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating file cost: {e}")
            return None
    
    def calculate_project_cost(self, project: Project) -> Optional[CostBreakdown]:
        """Calculate total cost for a project.
        
        Args:
            project: Project with analysis data
            
        Returns:
            Optional[CostBreakdown]: Project cost breakdown or None if failed
        """
        try:
            if not project.has_analysis_data():
                self.logger.error("Project has no analysis data")
                return None
            
            # Get language pair ID
            language_pair = self.language_pair_repository.get_or_create(
                project.source_language, project.target_language
            )
            
            if not language_pair:
                self.logger.error(f"Could not resolve language pair for project")
                return None
            
            # Get rates
            rates = self._get_rates_for_calculation(
                project.translator_id, language_pair.id, project.client_id
            )
            
            if not rates:
                self.logger.error("No rates found for project calculation")
                return None
            
            # Aggregate all file data
            aggregated_analysis = self._aggregate_project_analysis(project.analysis_data)
            
            # Calculate breakdown
            breakdown = self._calculate_breakdown(
                aggregated_analysis, rates, project.mt_percentage, project.client_id
            )
            
            if breakdown:
                # Apply project-level minimum fee if configured
                project_minimum_fee = self._get_project_minimum_fee(
                    project.translator_id, project.client_id
                )
                
                if project_minimum_fee and project_minimum_fee > breakdown.total_cost:
                    breakdown.minimum_fee = project_minimum_fee
                    breakdown.total_cost = project_minimum_fee
                    breakdown.minimum_fee_applied = True
            
            return breakdown
            
        except Exception as e:
            self.logger.error(f"Error calculating project cost: {e}")
            return None
    
    def calculate_multiple_files_cost(self, file_analyses: List[FileAnalysisData],
                                    translator_id: int, client_id: Optional[int] = None,
                                    mt_percentage: int = 70) -> Optional[CostBreakdown]:
        """Calculate cost for multiple files.
        
        Args:
            file_analyses: List of file analysis data
            translator_id: Translator ID
            client_id: Optional client ID
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Optional[CostBreakdown]: Combined cost breakdown
        """
        if not file_analyses:
            return None
        
        try:
            # Assume all files have the same language pair (take from first file)
            first_file = file_analyses[0]
            language_pair = self.language_pair_repository.get_or_create(
                first_file.source_language, first_file.target_language
            )
            
            if not language_pair:
                self.logger.error("Could not resolve language pair for multiple files")
                return None
            
            # Get rates
            rates = self._get_rates_for_calculation(
                translator_id, language_pair.id, client_id
            )
            
            if not rates:
                return None
            
            # Aggregate all files
            aggregated_analysis = self._aggregate_multiple_files(file_analyses)
            
            # Calculate breakdown
            return self._calculate_breakdown(
                aggregated_analysis, rates, mt_percentage, client_id
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating multiple files cost: {e}")
            return None
    
    def get_rate_preview(self, translator_id: int, language_pair_code: str,
                        client_id: Optional[int] = None) -> Dict[str, Any]:
        """Get rate preview for a translator and language pair.
        
        Args:
            translator_id: Translator ID
            language_pair_code: Language pair as "source>target"
            client_id: Optional client ID
            
        Returns:
            Dict[str, Any]: Rate preview information
        """
        try:
            # Parse language pair
            if '>' not in language_pair_code:
                return {'error': 'Invalid language pair format'}
            
            source_lang, target_lang = language_pair_code.split('>', 1)
            
            # Get or create language pair
            language_pair = self.language_pair_repository.get_or_create(
                source_lang.strip(), target_lang.strip()
            )
            
            if not language_pair:
                return {'error': 'Could not resolve language pair'}
            
            # Get rates
            rates = self._get_rates_for_calculation(
                translator_id, language_pair.id, client_id
            )
            
            if not rates:
                return {'error': 'No rates found'}
            
            # Format rate preview
            rate_preview = {
                'language_pair': language_pair_code,
                'client_specific': client_id is not None,
                'rates': {}
            }
            
            for category, rate in rates.items():
                rate_preview['rates'][category.value] = {
                    'rate_per_word': float(rate.rate_per_word),
                    'minimum_fee': float(rate.minimum_fee) if rate.is_minimum_fee_enabled else None,
                    'currency': rate.currency
                }
            
            return rate_preview
            
        except Exception as e:
            self.logger.error(f"Error getting rate preview: {e}")
            return {'error': str(e)}
    
    def _get_rates_for_calculation(self, translator_id: int, language_pair_id: int,
                                  client_id: Optional[int] = None) -> Dict[MatchCategoryType, Rate]:
        """Get rates for calculation using hierarchy resolution.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            client_id: Optional client ID
            
        Returns:
            Dict[MatchCategoryType, Rate]: Rates by category
        """
        rates = {}
        category_mapping = self.match_category_repository.get_category_mapping()
        
        for category_name, category_id in category_mapping.items():
            category_type = MatchCategoryType.from_display_name(category_name)
            
            if category_type:
                rate = self.rate_repository.find_rate_for_project(
                    translator_id, language_pair_id, category_id, client_id
                )
                
                if rate:
                    rates[category_type] = rate
                else:
                    # Use default rate if no specific rate found
                    default_rate_value = category_type.get_default_rate()
                    default_rate = Rate(
                        translator_id=translator_id,
                        language_pair_id=language_pair_id,
                        match_category_id=category_id,
                        rate_per_word=Decimal(str(default_rate_value))
                    )
                    rates[category_type] = default_rate
                    
                    self.logger.warning(
                        f"Using default rate for {category_name}: {default_rate_value}"
                    )
        
        return rates
    
    def _calculate_breakdown(self, analysis: FileAnalysisData, 
                           rates: Dict[MatchCategoryType, Rate],
                           mt_percentage: int, client_id: Optional[int]) -> CostBreakdown:
        """Calculate detailed cost breakdown.
        
        Args:
            analysis: File analysis data
            rates: Rates by category
            mt_percentage: MT percentage for 100% matches
            client_id: Optional client ID
            
        Returns:
            CostBreakdown: Detailed breakdown
        """
        category_costs = {}
        subtotal = Decimal('0.00')
        
        for category_type, category_data in analysis.categories.items():
            if category_data.words <= 0 or category_type not in rates:
                continue
            
            rate = rates[category_type]
            
            # Handle MT/TM breakdown for 100% matches
            if category_type.supports_mt_breakdown():
                word_breakdown = category_data.get_cost_calculation_words(mt_percentage)
                
                if word_breakdown['mt'] > 0:
                    # Use MT rate for MT words, TM rate for TM words
                    tm_rate = rate.rate_per_word
                    mt_rate = rates.get(MatchCategoryType.MT_MATCH, rate).rate_per_word
                    
                    tm_cost = Decimal(str(word_breakdown['tm'])) * tm_rate
                    mt_cost = Decimal(str(word_breakdown['mt'])) * mt_rate
                    total_cost = tm_cost + mt_cost
                    
                    category_costs[category_type.value] = {
                        'total_words': category_data.words,
                        'tm_words': word_breakdown['tm'],
                        'mt_words': word_breakdown['mt'],
                        'tm_rate': float(tm_rate),
                        'mt_rate': float(mt_rate),
                        'tm_cost': float(tm_cost),
                        'mt_cost': float(mt_cost),
                        'total_cost': float(total_cost),
                        'segments': category_data.segments,
                        'percent': category_data.percent
                    }
                    
                    subtotal += total_cost
                    continue
            
            # Standard calculation
            cost = Decimal(str(category_data.words)) * rate.rate_per_word
            
            category_costs[category_type.value] = {
                'words': category_data.words,
                'rate': float(rate.rate_per_word),
                'cost': float(cost),
                'segments': category_data.segments,
                'percent': category_data.percent
            }
            
            subtotal += cost
        
        # Calculate final total (minimum fee will be applied at project level if needed)
        total_cost = subtotal
        minimum_fee = Decimal('0.00')
        minimum_fee_applied = False
        
        return CostBreakdown(
            category_costs=category_costs,
            subtotal=subtotal,
            minimum_fee=minimum_fee,
            total_cost=total_cost,
            minimum_fee_applied=minimum_fee_applied,
            total_words=analysis.get_total_words(),
            total_segments=analysis.get_total_segments(),
            mt_percentage=mt_percentage
        )
    
    def _aggregate_project_analysis(self, project_analysis: ProjectAnalysisData) -> FileAnalysisData:
        """Aggregate project analysis data into single file analysis.
        
        Args:
            project_analysis: Project analysis data
            
        Returns:
            FileAnalysisData: Aggregated analysis
        """
        if not project_analysis.files:
            # Return empty analysis
            return FileAnalysisData(
                filename="Empty Project",
                source_language="",
                target_language=""
            )
        
        # Take language pair from first file
        first_file = project_analysis.files[0]
        
        # Create aggregated analysis
        aggregated = FileAnalysisData(
            filename=f"{project_analysis.project_name} (Aggregated)",
            source_language=first_file.source_language,
            target_language=first_file.target_language
        )
        
        # Get aggregated categories from project analysis
        aggregated_categories = project_analysis.get_aggregated_categories()
        
        # Set category data
        for category_type, category_data in aggregated_categories.items():
            aggregated.set_category_data(category_type, category_data)
        
        return aggregated
    
    def _aggregate_multiple_files(self, file_analyses: List[FileAnalysisData]) -> FileAnalysisData:
        """Aggregate multiple file analyses into single analysis.
        
        Args:
            file_analyses: List of file analyses
            
        Returns:
            FileAnalysisData: Aggregated analysis
        """
        if not file_analyses:
            return FileAnalysisData(filename="Empty", source_language="", target_language="")
        
        # Take language pair from first file
        first_file = file_analyses[0]
        
        # Create aggregated analysis
        aggregated = FileAnalysisData(
            filename=f"Multiple Files ({len(file_analyses)} files)",
            source_language=first_file.source_language,
            target_language=first_file.target_language
        )
        
        # Aggregate categories across all files
        from core.models.analysis import MatchCategoryData
        
        for category_type in MatchCategoryType.get_standard_categories():
            total_segments = 0
            total_words = 0
            total_characters = 0
            total_placeables = 0
            total_tm_words = 0
            total_mt_words = 0
            has_tm_mt_breakdown = False
            
            for file_analysis in file_analyses:
                category_data = file_analysis.get_category_data(category_type)
                total_segments += category_data.segments
                total_words += category_data.words
                total_characters += category_data.characters
                total_placeables += category_data.placeables
                
                if category_data.has_tm_mt_breakdown():
                    has_tm_mt_breakdown = True
                    total_tm_words += category_data.tm_words or 0
                    total_mt_words += category_data.mt_words or 0
            
            # Calculate percentage
            total_all_words = sum(
                sum(f.get_category_data(cat).words for cat in MatchCategoryType.get_standard_categories())
                for f in file_analyses
            )
            percent = (total_words / total_all_words * 100) if total_all_words > 0 else 0.0
            
            # Create aggregated category data
            aggregated_category = MatchCategoryData(
                category=category_type,
                segments=total_segments,
                words=total_words,
                characters=total_characters,
                placeables=total_placeables,
                percent=percent
            )
            
            if has_tm_mt_breakdown:
                aggregated_category.tm_words = total_tm_words
                aggregated_category.mt_words = total_mt_words
            
            aggregated.set_category_data(category_type, aggregated_category)
        
        return aggregated
    
    def _get_project_minimum_fee(self, translator_id: int, 
                                client_id: Optional[int] = None) -> Optional[Decimal]:
        """Get project-level minimum fee if configured.
        
        Args:
            translator_id: Translator ID
            client_id: Optional client ID
            
        Returns:
            Optional[Decimal]: Minimum fee or None
        """
        # For now, return None as project-level minimum fees
        # would be implemented in a future enhancement
        # This would typically check translator/client settings
        return None
    
    def validate_calculation_inputs(self, translator_id: int, 
                                  source_language: str, target_language: str,
                                  client_id: Optional[int] = None) -> Dict[str, Any]:
        """Validate inputs for calculation.
        
        Args:
            translator_id: Translator ID
            source_language: Source language code
            target_language: Target language code
            client_id: Optional client ID
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if language pair exists or can be created
            language_pair = self.language_pair_repository.find_by_languages(
                source_language, target_language
            )
            
            if not language_pair:
                # Try to create it
                language_pair = self.language_pair_repository.get_or_create(
                    source_language, target_language
                )
                
                if not language_pair:
                    validation['errors'].append('Invalid language pair')
                    validation['valid'] = False
                    return validation
            
            # Check if rates exist
            rates = self._get_rates_for_calculation(
                translator_id, language_pair.id, client_id
            )
            
            if not rates:
                validation['errors'].append('No rates found for translator and language pair')
                validation['valid'] = False
            else:
                # Check for default rate usage
                default_rate_count = 0
                for category, rate in rates.items():
                    if rate.id is None:  # Default rate (not persisted)
                        default_rate_count += 1
                
                if default_rate_count > 0:
                    validation['warnings'].append(
                        f'Using default rates for {default_rate_count} categories'
                    )
            
            return validation
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f'Validation error: {e}')
            return validation