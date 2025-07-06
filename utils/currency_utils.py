"""
Translation Cost Calculator - Currency Utilities

Utilities for currency formatting, conversion, and display.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Union

from config.settings import Settings


class CurrencyFormatter:
    """Handles currency formatting and display."""
    
    def __init__(self, currency: str = "EUR", decimal_places: int = 2):
        """Initialize currency formatter.
        
        Args:
            currency: Currency code (default: EUR)
            decimal_places: Number of decimal places for display
        """
        self.currency = currency
        self.decimal_places = decimal_places
        self.logger = logging.getLogger(__name__)
    
    def format_amount(self, amount: Union[Decimal, float, str], 
                     include_symbol: bool = True,
                     include_currency_code: bool = False) -> str:
        """Format amount for display.
        
        Args:
            amount: Amount to format
            include_symbol: Whether to include currency symbol
            include_currency_code: Whether to include currency code
            
        Returns:
            str: Formatted amount
        """
        try:
            # Convert to Decimal for precise formatting
            if isinstance(amount, str):
                decimal_amount = Decimal(amount.strip())
            elif isinstance(amount, float):
                decimal_amount = Decimal(str(amount))
            elif isinstance(amount, Decimal):
                decimal_amount = amount
            else:
                decimal_amount = Decimal('0.00')
            
            # Round to specified decimal places
            quantizer = Decimal('0.' + '0' * self.decimal_places)
            rounded_amount = decimal_amount.quantize(quantizer, rounding=ROUND_HALF_UP)
            
            # Format with thousand separators
            formatted = self._format_with_separators(rounded_amount)
            
            # Add currency symbol/code
            result = formatted
            
            if include_symbol:
                symbol = self.get_currency_symbol(self.currency)
                if self.currency in ['EUR', 'USD', 'GBP']:
                    result = f"{symbol}{formatted}"  # Symbol before amount
                else:
                    result = f"{formatted} {symbol}"  # Symbol after amount
            
            if include_currency_code:
                if include_symbol:
                    result = f"{result} {self.currency}"
                else:
                    result = f"{formatted} {self.currency}"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error formatting currency amount: {e}")
            return str(amount)
    
    def format_rate(self, rate: Union[Decimal, float, str], 
                   per_unit: str = "word") -> str:
        """Format rate for display.
        
        Args:
            rate: Rate to format
            per_unit: Unit for rate (e.g., 'word', 'segment')
            
        Returns:
            str: Formatted rate
        """
        try:
            # Use higher precision for rates (4 decimal places)
            if isinstance(rate, str):
                decimal_rate = Decimal(rate.strip())
            elif isinstance(rate, float):
                decimal_rate = Decimal(str(rate))
            elif isinstance(rate, Decimal):
                decimal_rate = rate
            else:
                decimal_rate = Decimal('0.0000')
            
            # Round to 4 decimal places for rates
            quantizer = Decimal('0.0001')
            rounded_rate = decimal_rate.quantize(quantizer, rounding=ROUND_HALF_UP)
            
            # Format the rate
            formatted_amount = self.format_amount(rounded_rate, include_symbol=True)
            
            return f"{formatted_amount}/{per_unit}"
            
        except Exception as e:
            self.logger.error(f"Error formatting rate: {e}")
            return f"{rate}/{per_unit}"
    
    def _format_with_separators(self, amount: Decimal) -> str:
        """Format decimal with thousand separators.
        
        Args:
            amount: Decimal amount
            
        Returns:
            str: Formatted string with separators
        """
        # Convert to string with proper decimal places
        amount_str = f"{amount:.{self.decimal_places}f}"
        
        # Split into integer and decimal parts
        if '.' in amount_str:
            integer_part, decimal_part = amount_str.split('.')
        else:
            integer_part = amount_str
            decimal_part = '0' * self.decimal_places
        
        # Add thousand separators to integer part
        # Use space as thousand separator for international compatibility
        if len(integer_part) > 3:
            formatted_integer = ''
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    formatted_integer = ' ' + formatted_integer
                formatted_integer = digit + formatted_integer
        else:
            formatted_integer = integer_part
        
        # Combine parts
        if self.decimal_places > 0:
            return f"{formatted_integer}.{decimal_part}"
        else:
            return formatted_integer
    
    @staticmethod
    def get_currency_symbol(currency_code: str) -> str:
        """Get currency symbol for currency code.
        
        Args:
            currency_code: Currency code (e.g., 'EUR', 'USD')
            
        Returns:
            str: Currency symbol
        """
        symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CHF': 'Fr',
            'CAD': 'C$',
            'AUD': 'A$',
            'SEK': 'kr',
            'NOK': 'kr',
            'DKK': 'kr',
            'PLN': 'zł',
            'CZK': 'Kč',
            'HUF': 'Ft'
        }
        
        return symbols.get(currency_code.upper(), currency_code)
    
    @staticmethod
    def parse_amount(amount_str: str) -> Optional[Decimal]:
        """Parse amount string to Decimal.
        
        Args:
            amount_str: String representation of amount
            
        Returns:
            Optional[Decimal]: Parsed amount or None if invalid
        """
        try:
            # Clean the string
            cleaned = amount_str.strip()
            
            # Remove currency symbols and codes
            symbols_to_remove = ['€', '$', '£', '¥', 'Fr', 'kr', 'zł', 'Kč', 'Ft']
            for symbol in symbols_to_remove:
                cleaned = cleaned.replace(symbol, '').strip()
            
            # Remove common currency codes
            currency_codes = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 
                            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF']
            for code in currency_codes:
                cleaned = cleaned.replace(code, '').strip()
            
            # Remove thousand separators (spaces)
            cleaned = cleaned.replace(' ', '')
            
            # Handle comma as decimal separator (European format)
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                # Assume comma is thousand separator, dot is decimal
                # Remove commas
                cleaned = cleaned.replace(',', '')
            
            # Parse as Decimal
            return Decimal(cleaned)
            
        except Exception:
            return None


class CurrencyConverter:
    """Handles currency conversion (stub for future implementation)."""
    
    def __init__(self):
        """Initialize currency converter."""
        self.logger = logging.getLogger(__name__)
        self.rates = {}  # Exchange rates cache
    
    def convert(self, amount: Decimal, from_currency: str, 
               to_currency: str) -> Optional[Decimal]:
        """Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Optional[Decimal]: Converted amount or None if conversion failed
        """
        # STUB: Currency conversion would require exchange rate API
        # For now, return amount unchanged if same currency
        if from_currency.upper() == to_currency.upper():
            return amount
        
        self.logger.warning(f"Currency conversion not implemented: {from_currency} -> {to_currency}")
        return None
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get exchange rate between currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Optional[Decimal]: Exchange rate or None if not available
        """
        # STUB: Would fetch from exchange rate API
        if from_currency.upper() == to_currency.upper():
            return Decimal('1.00')
        
        return None


class CostDisplayHelper:
    """Helper for displaying cost information in UI."""
    
    def __init__(self, currency: str = "EUR"):
        """Initialize cost display helper.
        
        Args:
            currency: Currency for formatting
        """
        self.formatter = CurrencyFormatter(currency)
        self.converter = CurrencyConverter()
    
    def format_cost_breakdown(self, breakdown: Dict[str, any]) -> Dict[str, str]:
        """Format cost breakdown for display.
        
        Args:
            breakdown: Cost breakdown data
            
        Returns:
            Dict[str, str]: Formatted breakdown
        """
        formatted = {}
        
        try:
            # Format category costs
            if 'category_costs' in breakdown:
                formatted['categories'] = {}
                for category, data in breakdown['category_costs'].items():
                    if 'total_cost' in data:
                        # MT/TM breakdown
                        formatted['categories'][category] = {
                            'total_words': f"{data['total_words']:,}",
                            'tm_words': f"{data.get('tm_words', 0):,}",
                            'mt_words': f"{data.get('mt_words', 0):,}",
                            'tm_rate': self.formatter.format_rate(data.get('tm_rate', 0)),
                            'mt_rate': self.formatter.format_rate(data.get('mt_rate', 0)),
                            'tm_cost': self.formatter.format_amount(data.get('tm_cost', 0)),
                            'mt_cost': self.formatter.format_amount(data.get('mt_cost', 0)),
                            'total_cost': self.formatter.format_amount(data['total_cost'])
                        }
                    else:
                        # Standard breakdown
                        formatted['categories'][category] = {
                            'words': f"{data.get('words', 0):,}",
                            'rate': self.formatter.format_rate(data.get('rate', 0)),
                            'cost': self.formatter.format_amount(data.get('cost', 0))
                        }
            
            # Format totals
            formatted['subtotal'] = self.formatter.format_amount(
                breakdown.get('subtotal', 0)
            )
            formatted['minimum_fee'] = self.formatter.format_amount(
                breakdown.get('minimum_fee', 0)
            )
            formatted['total_cost'] = self.formatter.format_amount(
                breakdown.get('total_cost', 0)
            )
            
            # Additional info
            formatted['total_words'] = f"{breakdown.get('total_words', 0):,}"
            formatted['total_segments'] = f"{breakdown.get('total_segments', 0):,}"
            formatted['mt_percentage'] = f"{breakdown.get('mt_percentage', 70)}%"
            
            return formatted
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error formatting cost breakdown: {e}")
            return {'error': 'Formatting error'}
    
    def format_rate_table(self, rates: Dict[str, any]) -> Dict[str, str]:
        """Format rate table for display.
        
        Args:
            rates: Rate data
            
        Returns:
            Dict[str, str]: Formatted rates
        """
        formatted = {}
        
        try:
            for category, rate_data in rates.items():
                if isinstance(rate_data, dict):
                    formatted[category] = {
                        'rate': self.formatter.format_rate(rate_data.get('rate_per_word', 0)),
                        'minimum_fee': self.formatter.format_amount(
                            rate_data.get('minimum_fee', 0)
                        ) if rate_data.get('minimum_fee') else 'None'
                    }
                else:
                    formatted[category] = self.formatter.format_rate(rate_data)
            
            return formatted
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error formatting rate table: {e}")
            return {'error': 'Formatting error'}
    
    def create_cost_summary(self, total_cost: Union[Decimal, float], 
                          total_words: int, currency: str = "EUR") -> str:
        """Create cost summary text.
        
        Args:
            total_cost: Total cost amount
            total_words: Total word count
            currency: Currency code
            
        Returns:
            str: Formatted summary
        """
        try:
            formatted_cost = self.formatter.format_amount(total_cost)
            formatted_words = f"{total_words:,}"
            
            # Calculate average rate per word
            if total_words > 0:
                avg_rate = Decimal(str(total_cost)) / Decimal(str(total_words))
                formatted_avg = self.formatter.format_rate(avg_rate)
                
                return (f"Total: {formatted_cost} for {formatted_words} words "
                       f"(avg. {formatted_avg})")
            else:
                return f"Total: {formatted_cost}"
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error creating cost summary: {e}")
            return f"Total: {total_cost}"


# Convenience functions
def format_currency(amount: Union[Decimal, float, str], 
                   currency: str = "EUR") -> str:
    """Format currency amount using default settings.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        str: Formatted amount
    """
    formatter = CurrencyFormatter(currency, Settings.CURRENCY_DECIMAL_PLACES)
    return formatter.format_amount(amount)


def format_rate(rate: Union[Decimal, float, str], 
               currency: str = "EUR", per_unit: str = "word") -> str:
    """Format rate using default settings.
    
    Args:
        rate: Rate to format
        currency: Currency code
        per_unit: Unit for rate
        
    Returns:
        str: Formatted rate
    """
    formatter = CurrencyFormatter(currency, 4)  # 4 decimal places for rates
    return formatter.format_rate(rate, per_unit)


def parse_currency_input(input_str: str) -> Optional[Decimal]:
    """Parse currency input string.
    
    Args:
        input_str: Input string
        
    Returns:
        Optional[Decimal]: Parsed amount or None
    """
    return CurrencyFormatter.parse_amount(input_str)


def get_default_currency() -> str:
    """Get default currency from settings.
    
    Returns:
        str: Default currency code
    """
    return Settings.CURRENCY_SYMBOL.replace('€', 'EUR').replace('$', 'USD').replace('£', 'GBP')