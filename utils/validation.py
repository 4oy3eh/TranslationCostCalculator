"""
Translation Cost Calculator - Input Validation Utilities

Comprehensive validation utilities for user inputs, file data, and business rules.
"""

import re
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from config.settings import Settings


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None, 
                 warnings: Optional[List[str]] = None):
        """Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, message: str) -> None:
        """Add an error message.
        
        Args:
            message: Error message to add
        """
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message.
        
        Args:
            message: Warning message to add
        """
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge with another validation result.
        
        Args:
            other: Other validation result to merge
            
        Returns:
            ValidationResult: Combined result
        """
        combined = ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings
        )
        return combined
    
    def __bool__(self) -> bool:
        """Boolean representation (True if valid)."""
        return self.is_valid
    
    def __str__(self) -> str:
        """String representation."""
        if self.is_valid:
            warning_text = f" (Warnings: {len(self.warnings)})" if self.warnings else ""
            return f"Valid{warning_text}"
        else:
            return f"Invalid: {'; '.join(self.errors)}"


class InputValidator:
    """Validates various types of user input."""
    
    def __init__(self):
        """Initialize input validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_translator_name(self, name: str) -> ValidationResult:
        """Validate translator name.
        
        Args:
            name: Translator name to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        if not name or not name.strip():
            result.add_error("Translator name is required")
            return result
        
        name = name.strip()
        rules = Settings.VALIDATION_RULES['translator_name']
        
        if len(name) < rules['min_length']:
            result.add_error(f"Name must be at least {rules['min_length']} characters")
        
        if len(name) > rules['max_length']:
            result.add_error(f"Name must be no more than {rules['max_length']} characters")
        
        # Check for potentially problematic characters
        if re.search(r'[<>"\|]', name):
            result.add_warning("Name contains special characters that might cause issues")
        
        return result
    
    def validate_email(self, email: Optional[str]) -> ValidationResult:
        """Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        if not email:
            return result  # Email is optional
        
        email = email.strip().lower()
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            result.add_error("Invalid email format")
        
        if len(email) > 320:  # RFC 5321 limit
            result.add_error("Email address is too long")
        
        return result
    
    def validate_project_name(self, name: str) -> ValidationResult:
        """Validate project name.
        
        Args:
            name: Project name to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        if not name or not name.strip():
            result.add_error("Project name is required")
            return result
        
        name = name.strip()
        rules = Settings.VALIDATION_RULES['project_name']
        
        if len(name) < rules['min_length']:
            result.add_error(f"Project name must be at least {rules['min_length']} character")
        
        if len(name) > rules['max_length']:
            result.add_error(f"Project name must be no more than {rules['max_length']} characters")
        
        # Check for filesystem-unsafe characters
        unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
        if re.search(unsafe_chars, name):
            result.add_error("Project name contains characters that are not allowed")
        
        return result
    
    def validate_rate_value(self, rate: Union[str, float, Decimal]) -> ValidationResult:
        """Validate rate per word value.
        
        Args:
            rate: Rate value to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        try:
            if isinstance(rate, str):
                rate_decimal = Decimal(rate.strip())
            elif isinstance(rate, float):
                rate_decimal = Decimal(str(rate))
            elif isinstance(rate, Decimal):
                rate_decimal = rate
            else:
                result.add_error("Rate must be a number")
                return result
            
            rules = Settings.VALIDATION_RULES['rate_value']
            
            if rate_decimal < Decimal(str(rules['min_value'])):
                result.add_error(f"Rate cannot be negative")
            
            if rate_decimal > Decimal(str(rules['max_value'])):
                result.add_error(f"Rate cannot exceed {rules['max_value']} EUR per word")
            
            # Check decimal places
            if rate_decimal != rate_decimal.quantize(Decimal('0.0001')):
                result.add_warning("Rate will be rounded to 4 decimal places")
            
            # Reasonable rate warnings
            if rate_decimal > Decimal('1.0'):
                result.add_warning("Rate seems unusually high (>1 EUR per word)")
            
        except (InvalidOperation, ValueError):
            result.add_error("Invalid rate format - must be a valid number")
        
        return result
    
    def validate_minimum_fee(self, fee: Union[str, float, Decimal]) -> ValidationResult:
        """Validate minimum fee value.
        
        Args:
            fee: Minimum fee to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        try:
            if isinstance(fee, str):
                fee_decimal = Decimal(fee.strip())
            elif isinstance(fee, float):
                fee_decimal = Decimal(str(fee))
            elif isinstance(fee, Decimal):
                fee_decimal = fee
            else:
                result.add_error("Minimum fee must be a number")
                return result
            
            rules = Settings.VALIDATION_RULES['minimum_fee']
            
            if fee_decimal < Decimal(str(rules['min_value'])):
                result.add_error("Minimum fee cannot be negative")
            
            if fee_decimal > Decimal(str(rules['max_value'])):
                result.add_error(f"Minimum fee cannot exceed {rules['max_value']} EUR")
            
            # Check decimal places
            if fee_decimal != fee_decimal.quantize(Decimal('0.01')):
                result.add_warning("Minimum fee will be rounded to 2 decimal places")
            
        except (InvalidOperation, ValueError):
            result.add_error("Invalid minimum fee format - must be a valid number")
        
        return result
    
    def validate_mt_percentage(self, percentage: Union[str, int]) -> ValidationResult:
        """Validate MT percentage value.
        
        Args:
            percentage: MT percentage to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        try:
            if isinstance(percentage, str):
                percentage_int = int(percentage.strip())
            else:
                percentage_int = int(percentage)
            
            rules = Settings.VALIDATION_RULES['mt_percentage']
            
            if percentage_int < rules['min_value']:
                result.add_error("MT percentage cannot be less than 0")
            
            if percentage_int > rules['max_value']:
                result.add_error("MT percentage cannot be more than 100")
            
        except (ValueError, TypeError):
            result.add_error("MT percentage must be a whole number")
        
        return result
    
    def validate_language_code(self, language_code: str) -> ValidationResult:
        """Validate language code.
        
        Args:
            language_code: Language code to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        if not language_code or not language_code.strip():
            result.add_error("Language code is required")
            return result
        
        language_code = language_code.strip().lower()
        
        # Check format (2-5 characters, letters and underscores)
        if not re.match(r'^[a-z_]{2,5}$', language_code):
            result.add_error("Language code must be 2-5 characters (letters and underscores only)")
        
        # Check if it's in our supported languages
        if language_code not in Settings.SUPPORTED_LANGUAGES:
            result.add_warning(f"Language code '{language_code}' is not in the supported languages list")
        
        return result


class FileValidator:
    """Validates file-related inputs and constraints."""
    
    def __init__(self):
        """Initialize file validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_upload_file(self, file_path: Path) -> ValidationResult:
        """Validate uploaded file.
        
        Args:
            file_path: Path to uploaded file
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Basic existence check
        if not file_path.exists():
            result.add_error("File does not exist")
            return result
        
        if not file_path.is_file():
            result.add_error("Path is not a file")
            return result
        
        # Size validation
        max_size_mb = Settings.VALIDATION_RULES.get('max_file_size_mb', 50)
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                result.add_error(f"File size ({size_mb:.1f} MB) exceeds maximum ({max_size_mb} MB)")
        except OSError:
            result.add_error("Cannot read file size")
        
        # Extension validation
        try:
            # Import here to avoid circular dependency
            from parsers.parser_factory import get_supported_extensions
            supported_extensions = get_supported_extensions()
        except ImportError:
            # Fallback if parsers not available
            supported_extensions = ['.csv', '.json', '.xlsx']
        
        if file_path.suffix.lower() not in supported_extensions:
            result.add_warning(
                f"File extension '{file_path.suffix}' is not in supported list: {supported_extensions}"
            )
        
        # Filename validation
        from utils.file_utils import FileUtils
        if not FileUtils.is_safe_filename(file_path.name):
            result.add_error("Filename contains unsafe characters")
        
        return result
    
    def validate_file_content_basic(self, file_path: Path) -> ValidationResult:
        """Basic validation of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        try:
            # Check if file is empty
            if file_path.stat().st_size == 0:
                result.add_error("File is empty")
                return result
            
            # Try to read first few bytes to check if file is readable
            with open(file_path, 'rb') as f:
                first_bytes = f.read(1024)
            
            # Check for null bytes (binary file indicator)
            if b'\x00' in first_bytes:
                result.add_warning("File appears to be binary")
            
            # Try to decode as text
            try:
                first_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    first_bytes.decode('latin1')
                except UnicodeDecodeError:
                    result.add_warning("File encoding may not be supported")
            
        except Exception as e:
            result.add_error(f"Cannot read file: {e}")
        
        return result


class BusinessRuleValidator:
    """Validates business rules and data consistency."""
    
    def __init__(self):
        """Initialize business rule validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_rate_combination(self, translator_id: int, client_id: Optional[int],
                                 language_pair_id: int, match_category_id: int) -> ValidationResult:
        """Validate that rate combination doesn't already exist.
        
        Args:
            translator_id: Translator ID
            client_id: Client ID (optional)
            language_pair_id: Language pair ID
            match_category_id: Match category ID
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Basic ID validation
        if translator_id <= 0:
            result.add_error("Invalid translator ID")
        
        if language_pair_id <= 0:
            result.add_error("Invalid language pair ID")
        
        if match_category_id <= 0:
            result.add_error("Invalid match category ID")
        
        if client_id is not None and client_id <= 0:
            result.add_error("Invalid client ID")
        
        # Note: Actual duplicate checking would be done at repository level
        # This is just basic validation
        
        return result
    
    def validate_project_consistency(self, project_data: Dict[str, Any]) -> ValidationResult:
        """Validate project data consistency.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Check required fields
        required_fields = ['name', 'translator_id', 'source_language', 'target_language']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                result.add_error(f"Missing required field: {field}")
        
        # Validate MT percentage if present
        if 'mt_percentage' in project_data:
            mt_result = InputValidator().validate_mt_percentage(project_data['mt_percentage'])
            result = result.merge(mt_result)
        
        # Validate language codes
        for lang_field in ['source_language', 'target_language']:
            if lang_field in project_data:
                lang_result = InputValidator().validate_language_code(project_data[lang_field])
                result = result.merge(lang_result)
        
        # Check that source and target languages are different
        if (project_data.get('source_language') and 
            project_data.get('target_language') and
            project_data['source_language'] == project_data['target_language']):
            result.add_error("Source and target languages must be different")
        
        return result


# Convenience functions for common validations

def validate_input(input_type: str, value: Any) -> ValidationResult:
    """Convenience function for common input validation.
    
    Args:
        input_type: Type of input ('translator_name', 'email', 'project_name', etc.)
        value: Value to validate
        
    Returns:
        ValidationResult: Validation result
    """
    validator = InputValidator()
    
    validation_methods = {
        'translator_name': validator.validate_translator_name,
        'email': validator.validate_email,
        'project_name': validator.validate_project_name,
        'rate_value': validator.validate_rate_value,
        'minimum_fee': validator.validate_minimum_fee,
        'mt_percentage': validator.validate_mt_percentage,
        'language_code': validator.validate_language_code
    }
    
    if input_type in validation_methods:
        return validation_methods[input_type](value)
    else:
        result = ValidationResult()
        result.add_error(f"Unknown validation type: {input_type}")
        return result


def validate_file(file_path: Path, check_content: bool = True) -> ValidationResult:
    """Convenience function for file validation.
    
    Args:
        file_path: Path to file
        check_content: Whether to perform content validation
        
    Returns:
        ValidationResult: Validation result
    """
    file_validator = FileValidator()
    
    result = file_validator.validate_upload_file(file_path)
    
    if check_content and result.is_valid:
        content_result = file_validator.validate_file_content_basic(file_path)
        result = result.merge(content_result)
    
    return result