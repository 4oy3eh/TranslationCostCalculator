"""
Translation Cost Calculator - Application Settings

Centralized configuration for the application including database paths,
UI constants, default values, and file format specifications.
"""

from pathlib import Path
from typing import Dict, List


class Settings:
    """Application configuration constants and settings."""
    
    # =============================================================================
    # APPLICATION METADATA
    # =============================================================================
    
    APP_NAME = "Translation Cost Calculator"
    APP_VERSION = "1.0.0"
    ORGANIZATION = "Translation Solutions"
    
    # =============================================================================
    # PATHS AND DIRECTORIES
    # =============================================================================
    
    # Base paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # Database
    DATABASE_FILE = DATA_DIR / "translation_calculator.db"
    MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    DATABASE_CONFIG = {
        "timeout": 30.0,  # Connection timeout in seconds
        "check_same_thread": False,  # Allow multi-threading
        "isolation_level": None,  # Autocommit mode
    }
    
    # =============================================================================
    # UI CONFIGURATION
    # =============================================================================
    
    # Main window
    MAIN_WINDOW_MIN_SIZE = (1200, 800)
    MAIN_WINDOW_DEFAULT_SIZE = (1400, 900)
    
    # Splitter proportions (left panel : right panel)
    SPLITTER_PROPORTIONS = [30, 70]  # 30% file list, 70% calculation
    
    # File dialog filters
    FILE_DIALOG_FILTERS = {
        "csv": "CSV Files (*.csv)",
        "json": "JSON Files (*.json)",
        "xlsx": "Excel Files (*.xlsx)",
        "all_supported": "All Supported (*.csv *.json *.xlsx)",
        "all_files": "All Files (*.*)"
    }
    
    # =============================================================================
    # BUSINESS LOGIC DEFAULTS
    # =============================================================================
    
    # Default MT percentage for 100% matches
    DEFAULT_MT_PERCENTAGE = 70
    
    # Default minimum fee status
    DEFAULT_MINIMUM_FEE_ENABLED = False
    DEFAULT_MINIMUM_FEE = 0.00
    
    # Default rates per word (EUR)
    DEFAULT_RATES = {
        "Context Match": 0.03,
        "Repetitions": 0.03,
        "100%": 0.05,
        "95% - 99%": 0.08,
        "85% - 94%": 0.10,
        "75% - 84%": 0.11,
        "50% - 74%": 0.12,
        "No Match": 0.12,
        "MT Match": 0.02
    }
    
    # Currency formatting
    CURRENCY_SYMBOL = "€"
    CURRENCY_DECIMAL_PLACES = 2
    
    # =============================================================================
    # FILE FORMAT SPECIFICATIONS
    # =============================================================================
    
    # Trados CSV format detection
    TRADOS_CSV_CONFIG = {
        "encoding": "utf-8-sig",  # UTF-8 with BOM support
        "delimiter": ";",
        "expected_headers": [
            "Context Match", "Repetitions", "100%", "95% - 99%",
            "85% - 94%", "75% - 84%", "50% - 74%", "No Match", "Total"
        ],
        "data_fields": ["Segments", "Words", "Placeables", "Percent"],
        "optional_fields": ["Characters"],  # May or may not be present
        "header_rows": 2,  # Two-line header system
        "format_variants": {
            "with_characters": 5,  # 5 semicolons between categories
            "without_characters": 4  # 4 semicolons between categories
        }
    }
    
    # Phrase JSON format
    PHRASE_JSON_CONFIG = {
        "encoding": "utf-8",
        "required_fields": ["projectName", "analyseLanguageParts"],
        "match_categories": {
            "contextMatch": "Context Match",
            "repetitions": "Repetitions", 
            "match100": "100%",
            "match95": "95% - 99%",
            "match85": "85% - 94%",
            "match75": "75% - 84%",
            "match50": "50% - 74%",
            "match0": "No Match"
        },
        "data_fields": ["segments", "words", "characters", "normalizedPages", "percent"],
        "special_fields": {
            "match100": ["sum", "tm", "mt", "nt"]  # TM/MT breakdown for 100% matches
        }
    }
    
    # Excel format (Phase 3)
    EXCEL_CONFIG = {
        "supported_extensions": [".xlsx", ".xls"],
        "max_header_rows": 10,  # Search first 10 rows for headers
        "min_data_rows": 1,
        "encoding": "utf-8"
    }
    
    # =============================================================================
    # EXPORT CONFIGURATION
    # =============================================================================
    
    # PDF export settings
    PDF_EXPORT_CONFIG = {
        "page_size": "A4",
        "margins": {
            "top": 72,    # 1 inch in points
            "bottom": 72,
            "left": 72,
            "right": 72
        },
        "fonts": {
            "title": "Helvetica-Bold",
            "heading": "Helvetica-Bold", 
            "body": "Helvetica",
            "table": "Helvetica"
        },
        "font_sizes": {
            "title": 16,
            "heading": 12,
            "body": 10,
            "table": 9
        },
        "colors": {
            "header": (0.2, 0.2, 0.2),  # Dark gray
            "border": (0.5, 0.5, 0.5),  # Medium gray
            "background": (0.95, 0.95, 0.95)  # Light gray
        }
    }
    
    # Excel export settings (Phase 3)
    EXCEL_EXPORT_CONFIG = {
        "sheet_names": {
            "summary": "Summary",
            "detailed": "Detailed Breakdown",
            "files": "File Analysis"
        },
        "include_charts": True,
        "include_formulas": True
    }
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": LOGS_DIR / "translation_calculator.log",
        "max_bytes": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5,
        "console_output": True
    }
    
    # =============================================================================
    # VALIDATION RULES
    # =============================================================================
    
    VALIDATION_RULES = {
        "translator_name": {
            "min_length": 2,
            "max_length": 100,
            "required": True
        },
        "project_name": {
            "min_length": 1,
            "max_length": 200,
            "required": True
        },
        "rate_value": {
            "min_value": 0.0,
            "max_value": 10.0,  # Max 10 EUR per word
            "decimal_places": 4
        },
        "minimum_fee": {
            "min_value": 0.0,
            "max_value": 10000.0,  # Max 10,000 EUR minimum fee
            "decimal_places": 2
        },
        "mt_percentage": {
            "min_value": 0,
            "max_value": 100,
            "default": DEFAULT_MT_PERCENTAGE
        }
    }
    
    # =============================================================================
    # SUPPORTED LANGUAGES
    # =============================================================================
    
    # Common language codes and display names
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "de": "German", 
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "pl": "Polish",
        "cs": "Czech",
        "sk": "Slovak",
        "hu": "Hungarian",
        "ro": "Romanian",
        "bg": "Bulgarian",
        "hr": "Croatian",
        "sl": "Slovenian",
        "et": "Estonian",
        "lv": "Latvian",
        "lt": "Lithuanian",
        "fi": "Finnish",
        "sv": "Swedish",
        "no": "Norwegian",
        "da": "Danish",
        "ru": "Russian",
        "uk": "Ukrainian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "he": "Hebrew",
        "tr": "Turkish",
        "th": "Thai",
        "vi": "Vietnamese",
        "hi": "Hindi"
    }