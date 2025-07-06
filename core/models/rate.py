"""
Translation Cost Calculator - Rate System Models

Rate models supporting hierarchical rate structure with client-specific rates,
minimum fees, and language pair management.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List

from core.models.match_category import MatchCategoryType


@dataclass
class LanguagePair:
    """Language pair model for rate organization."""
    
    id: Optional[int] = None
    source_language: str = ""
    target_language: str = ""
    
    def __post_init__(self):
        """Validate and normalize language codes."""
        self.source_language = self.source_language.strip().lower()
        self.target_language = self.target_language.strip().lower()
    
    def get_pair_code(self) -> str:
        """Get language pair in standard format.
        
        Returns:
            str: Language pair as "source>target"
        """
        return f"{self.source_language}>{self.target_language}"
    
    def get_display_name(self) -> str:
        """Get human-readable language pair name.
        
        Returns:
            str: Display name using language names from settings
        """
        from config.settings import Settings
        
        source_name = Settings.SUPPORTED_LANGUAGES.get(
            self.source_language, self.source_language.upper()
        )
        target_name = Settings.SUPPORTED_LANGUAGES.get(
            self.target_language, self.target_language.upper()
        )
        
        return f"{source_name} → {target_name}"
    
    def is_valid(self) -> bool:
        """Check if language pair is valid.
        
        Returns:
            bool: True if both languages are specified
        """
        return (
            bool(self.source_language) and
            bool(self.target_language) and
            self.source_language != self.target_language
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.
        
        Returns:
            dict: Language pair data
        """
        return {
            'id': self.id,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'pair_code': self.get_pair_code(),
            'display_name': self.get_display_name()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LanguagePair':
        """Create language pair from dictionary.
        
        Args:
            data: Dictionary containing language pair data
            
        Returns:
            LanguagePair: New instance
        """
        pair = cls()
        pair.id = data.get('id')
        pair.source_language = data.get('source_language', '')
        pair.target_language = data.get('target_language', '')
        return pair
    
    def __str__(self) -> str:
        """String representation."""
        return self.get_display_name()
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on language codes."""
        if not isinstance(other, LanguagePair):
            return False
        return (
            self.source_language == other.source_language and
            self.target_language == other.target_language
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.source_language, self.target_language))


@dataclass
class Rate:
    """Rate model with hierarchical structure support."""
    
    # Core identification
    id: Optional[int] = None
    translator_id: int = 0
    client_id: Optional[int] = None  # None for general rates
    language_pair_id: int = 0
    match_category_id: int = 0
    
    # Rate information
    rate_per_word: Decimal = Decimal('0.00')
    minimum_fee: Decimal = Decimal('0.00')
    is_minimum_fee_enabled: bool = False
    
    # Currency (future extension)
    currency: str = "EUR"
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related objects (not persisted)
    match_category: Optional[MatchCategoryType] = None
    language_pair: Optional[LanguagePair] = None
    
    def __post_init__(self):
        """Initialize default values and validate data."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Ensure non-negative values
        self.rate_per_word = max(Decimal('0.00'), self.rate_per_word)
        self.minimum_fee = max(Decimal('0.00'), self.minimum_fee)
        
        # Quantize to appropriate decimal places
        self.rate_per_word = self.rate_per_word.quantize(Decimal('0.0001'))
        self.minimum_fee = self.minimum_fee.quantize(Decimal('0.01'))
    
    def is_client_specific(self) -> bool:
        """Check if this is a client-specific rate.
        
        Returns:
            bool: True if rate is for specific client
        """
        return self.client_id is not None
    
    def is_valid(self) -> bool:
        """Check if rate has all required fields.
        
        Returns:
            bool: True if rate is valid
        """
        return (
            self.translator_id > 0 and
            self.language_pair_id > 0 and
            self.match_category_id > 0 and
            self.rate_per_word >= Decimal('0.00')
        )
    
    def get_effective_rate(self) -> Decimal:
        """Get the effective rate per word.
        
        Returns:
            Decimal: Rate per word
        """
        return self.rate_per_word
    
    def get_priority_level(self) -> int:
        """Get priority level for rate hierarchy.
        
        Returns:
            int: Priority level (lower = higher priority)
        """
        if self.is_client_specific():
            return 1  # Highest priority
        else:
            return 2  # General rate
    
    def calculate_cost(self, word_count: int) -> Decimal:
        """Calculate cost for given word count including minimum fee.
        
        Args:
            word_count: Number of words
            
        Returns:
            Decimal: Total cost
        """
        base_cost = Decimal(str(word_count)) * self.rate_per_word
        
        if self.is_minimum_fee_enabled and self.minimum_fee > base_cost:
            return self.minimum_fee
        
        return base_cost.quantize(Decimal('0.01'))
    
    def to_dict(self) -> dict:
        """Convert rate to dictionary for serialization.
        
        Returns:
            dict: Rate data as dictionary
        """
        return {
            'id': self.id,
            'translator_id': self.translator_id,
            'client_id': self.client_id,
            'language_pair_id': self.language_pair_id,
            'match_category_id': self.match_category_id,
            'rate_per_word': float(self.rate_per_word),
            'minimum_fee': float(self.minimum_fee),
            'is_minimum_fee_enabled': self.is_minimum_fee_enabled,
            'currency': self.currency,
            'is_client_specific': self.is_client_specific(),
            'priority_level': self.get_priority_level(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Rate':
        """Create rate from dictionary data.
        
        Args:
            data: Dictionary containing rate data
            
        Returns:
            Rate: New rate instance
        """
        rate = cls()
        rate.id = data.get('id')
        rate.translator_id = data.get('translator_id', 0)
        rate.client_id = data.get('client_id')
        rate.language_pair_id = data.get('language_pair_id', 0)
        rate.match_category_id = data.get('match_category_id', 0)
        rate.rate_per_word = Decimal(str(data.get('rate_per_word', '0.00')))
        rate.minimum_fee = Decimal(str(data.get('minimum_fee', '0.00')))
        rate.is_minimum_fee_enabled = data.get('is_minimum_fee_enabled', False)
        rate.currency = data.get('currency', 'EUR')
        
        # Parse datetime fields
        if data.get('created_at'):
            rate.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            rate.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return rate
    
    def update_rate(self, new_rate: Decimal, minimum_fee: Optional[Decimal] = None,
                   enable_minimum_fee: Optional[bool] = None) -> None:
        """Update rate values.
        
        Args:
            new_rate: New rate per word
            minimum_fee: New minimum fee (optional)
            enable_minimum_fee: Enable/disable minimum fee (optional)
        """
        self.rate_per_word = max(Decimal('0.00'), new_rate).quantize(Decimal('0.0001'))
        
        if minimum_fee is not None:
            self.minimum_fee = max(Decimal('0.00'), minimum_fee).quantize(Decimal('0.01'))
        
        if enable_minimum_fee is not None:
            self.is_minimum_fee_enabled = enable_minimum_fee
        
        self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        """String representation of the rate."""
        rate_type = "Client-specific" if self.is_client_specific() else "General"
        return f"{rate_type} Rate: {self.rate_per_word}/word"
    
    def __repr__(self) -> str:
        """Developer representation of the rate."""
        return (f"Rate(id={self.id}, translator_id={self.translator_id}, "
                f"client_id={self.client_id}, rate={self.rate_per_word})")


class RateCalculator:
    """Utility class for rate calculations and hierarchy resolution."""
    
    @staticmethod
    def resolve_rate_hierarchy(rates: List[Rate], translator_id: int,
                             language_pair_id: int, match_category_id: int,
                             client_id: Optional[int] = None) -> Optional[Rate]:
        """Resolve rate hierarchy to find the best applicable rate.
        
        Args:
            rates: List of available rates
            translator_id: Translator ID
            language_pair_id: Language pair ID
            match_category_id: Match category ID
            client_id: Optional client ID
            
        Returns:
            Optional[Rate]: Best applicable rate or None
        """
        # Filter applicable rates
        applicable_rates = [
            rate for rate in rates
            if (rate.translator_id == translator_id and
                rate.language_pair_id == language_pair_id and
                rate.match_category_id == match_category_id)
        ]
        
        if not applicable_rates:
            return None
        
        # Priority 1: Client-specific rate
        if client_id:
            client_rates = [
                rate for rate in applicable_rates
                if rate.client_id == client_id
            ]
            if client_rates:
                return client_rates[0]  # Should be unique
        
        # Priority 2: General rate (client_id is None)
        general_rates = [
            rate for rate in applicable_rates
            if rate.client_id is None
        ]
        if general_rates:
            return general_rates[0]  # Should be unique
        
        return None
    
    @staticmethod
    def calculate_project_cost(rates: Dict[MatchCategoryType, Rate],
                             word_counts: Dict[MatchCategoryType, int],
                             minimum_fee: Optional[Decimal] = None) -> Dict[str, any]:
        """Calculate total project cost with detailed breakdown.
        
        Args:
            rates: Rates by match category
            word_counts: Word counts by match category
            minimum_fee: Optional project minimum fee
            
        Returns:
            Dict: Detailed cost calculation
        """
        calculation = {
            'categories': {},
            'subtotal': Decimal('0.00'),
            'minimum_fee': minimum_fee or Decimal('0.00'),
            'total': Decimal('0.00'),
            'minimum_fee_applied': False
        }
        
        # Calculate cost by category
        for category, word_count in word_counts.items():
            if word_count <= 0:
                continue
            
            rate = rates.get(category)
            if not rate:
                continue
            
            category_cost = rate.calculate_cost(word_count)
            calculation['categories'][category.value] = {
                'words': word_count,
                'rate': float(rate.rate_per_word),
                'cost': float(category_cost)
            }
            calculation['subtotal'] += category_cost
        
        # Apply project minimum fee if applicable
        if minimum_fee and minimum_fee > calculation['subtotal']:
            calculation['total'] = minimum_fee
            calculation['minimum_fee_applied'] = True
        else:
            calculation['total'] = calculation['subtotal']
        
        # Convert Decimals to floats for JSON serialization
        calculation['subtotal'] = float(calculation['subtotal'])
        calculation['minimum_fee'] = float(calculation['minimum_fee'])
        calculation['total'] = float(calculation['total'])
        
        return calculation
    
    @staticmethod
    def get_default_rates(match_categories: List[MatchCategoryType]) -> Dict[MatchCategoryType, Decimal]:
        """Get default rates for match categories.
        
        Args:
            match_categories: List of match categories
            
        Returns:
            Dict: Default rates by category
        """
        from config.settings import Settings
        
        default_rates = {}
        for category in match_categories:
            rate_value = Settings.DEFAULT_RATES.get(category.value, 0.12)
            default_rates[category] = Decimal(str(rate_value))
        
        return default_rates