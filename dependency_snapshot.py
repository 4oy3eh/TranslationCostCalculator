"""
Translation Cost Calculator - Dependency Snapshot v1.4
Generated: Prompt 5 - Basic UI Framework & Main Window

This file tracks all project components and their dependencies.
Update after each prompt completion.
"""

# =============================================================================
# PROJECT STATUS
# =============================================================================

PROJECT_VERSION = "1.0.0-dev"
PHASE = "Phase 1: Core Infrastructure" 
CURRENT_PROMPT = "5 - Basic UI Framework & Main Window"
COMPLETION_STATUS = "FULLY_COMPLETED_AND_VERIFIED"

# =============================================================================
# SELF-CHECK RESULTS
# =============================================================================

SELF_CHECK = {
    "main_window_functional": True,
    "splitter_layout_implemented": True,
    "file_list_widget_complete": True,
    "calculation_widget_complete": True,
    "basic_styling_applied": True,
    "menu_bar_complete": True,
    "toolbar_functional": True,
    "status_bar_with_progress": True,
    "background_file_processing": True,
    "service_integration_working": True,
    "error_handling_comprehensive": True,
    "ui_responsive_and_intuitive": True,
    "expected_stubs_identified": True,
    "phase_1_mvp_complete": True,
    "parser_correctly_handles_different_formats": True,  
    "column_detection_working": True,  
    "file_format_distinction_verified": True
}

# =============================================================================
# IMPLEMENTED COMPONENTS
# =============================================================================

IMPLEMENTED = {
    # Core Models (Domain Layer)
    "core.models.match_category": {
        "status": "IMPLEMENTED",
        "classes": ["MatchCategoryType", "MatchCategoryMapping"],
        "dependencies": ["enum"],
        "description": "Match category enumeration with Phrase JSON mapping"
    },
    "core.models.analysis": {
        "status": "IMPLEMENTED", 
        "classes": ["FileAnalysisData", "MatchCategoryData", "ProjectAnalysisData"],
        "dependencies": ["dataclasses", "typing", "decimal", "core.models.match_category"],
        "description": "File analysis data models with TM/MT support and cost calculation"
    },
    "core.models.project": {
        "status": "IMPLEMENTED",
        "classes": ["Project", "ProjectFile"],
        "dependencies": ["dataclasses", "datetime", "typing", "decimal", "core.models.analysis"],
        "description": "Project domain model with analysis data integration and cost calculation"
    },
    "core.models.translator": {
        "status": "IMPLEMENTED",
        "classes": ["Translator", "Client"],
        "dependencies": ["dataclasses", "datetime", "typing", "re"],
        "description": "Translator and client domain models with validation"
    },
    "core.models.rate": {
        "status": "IMPLEMENTED",
        "classes": ["Rate", "LanguagePair", "RateCalculator"],
        "dependencies": ["dataclasses", "datetime", "decimal", "typing", "core.models.match_category"],
        "description": "Rate system with hierarchical support and calculation utilities"
    },
    
    # Configuration Layer
    "config.settings": {
        "status": "IMPLEMENTED",
        "classes": ["Settings"],
        "dependencies": ["pathlib", "typing"],
        "description": "Application configuration constants and validation rules"
    },
    "config.database": {
        "status": "IMPLEMENTED",
        "classes": ["DatabaseManager"],
        "dependencies": ["sqlite3", "pathlib", "logging", "typing"],
        "description": "Database configuration and connection management with migration support"
    },
    
    # Repository Layer (Data Access)
    "core.repositories.base_repository": {
        "status": "IMPLEMENTED",
        "classes": ["BaseRepository", "RepositoryError"],
        "dependencies": ["abc", "typing", "sqlite3", "logging", "dataclasses"],
        "description": "Abstract base repository with common CRUD operations"
    },
    "core.repositories.project_repository": {
        "status": "IMPLEMENTED",
        "classes": ["ProjectRepository", "ProjectFileRepository"],
        "dependencies": ["core.repositories.base_repository", "core.models.project", "core.models.analysis", "json", "datetime"],
        "description": "Project and project file data access with specialized queries"
    },
    "core.repositories.translator_repository": {
        "status": "IMPLEMENTED",
        "classes": ["TranslatorRepository", "ClientRepository"],
        "dependencies": ["core.repositories.base_repository", "core.models.translator", "datetime"],
        "description": "Translator and client data access with relationship queries"
    },
    "core.repositories.rate_repository": {
        "status": "IMPLEMENTED",
        "classes": ["RateRepository", "LanguagePairRepository", "MatchCategoryRepository"],
        "dependencies": ["core.repositories.base_repository", "core.models.rate", "core.models.match_category", "decimal", "logging"],
        "description": "Complete rate system data access with hierarchical resolution"
    },
    
    # Parser Layer
    "parsers.base_parser": {
        "status": "IMPLEMENTED",
        "classes": ["BaseParser", "ParserError"],
        "dependencies": ["abc", "pathlib", "typing", "logging", "core.models.analysis"],
        "description": "Abstract base parser with common functionality"
    },
    "parsers.column_detector": {
        "status": "IMPLEMENTED",
        "classes": ["TradosColumnDetector", "ColumnMapping"],
        "dependencies": ["logging", "typing", "dataclasses", "core.models.match_category"],
        "description": "Intelligent column detection for Trados CSV files"
    },
    "parsers.trados_csv_parser": {
        "status": "IMPLEMENTED",
        "classes": ["TradosCSVParser"],
        "dependencies": ["parsers.base_parser", "parsers.column_detector", "core.models.analysis", "core.models.match_category", "pathlib", "typing"],
        "description": "Complete Trados CSV parser supporting both format variations"
    },
    "parsers.parser_factory": {
        "status": "IMPLEMENTED",
        "classes": ["ParserFactory"],
        "functions": ["get_parser_factory", "parse_file", "can_parse_file", "get_supported_extensions"],
        "dependencies": ["logging", "pathlib", "typing", "parsers.base_parser", "parsers.trados_csv_parser", "core.models.analysis"],
        "description": "Extensible parser factory for multiple file formats"
    },
    
    # Business Services Layer
    "core.services.calculation_service": {
        "status": "IMPLEMENTED",
        "classes": ["CalculationService", "CostBreakdown"],
        "dependencies": ["logging", "decimal", "typing", "dataclasses", "core.models.analysis", "core.models.match_category", "core.models.project", "core.models.rate", "core.repositories.rate_repository", "config.database"],
        "description": "Core business logic for cost calculation with MT percentage handling and rate hierarchy"
    },
    "core.services.project_service": {
        "status": "IMPLEMENTED",
        "classes": ["ProjectService"],
        "dependencies": ["logging", "json", "pathlib", "typing", "datetime", "core.models.project", "core.models.analysis", "core.repositories.project_repository", "core.repositories.translator_repository", "core.repositories.rate_repository", "parsers.parser_factory", "utils.validation", "utils.file_utils", "config.database"],
        "description": "Project management service with file processing and validation"
    },
    
    # User Interface Layer (NEW)
    "ui.main_window": {
        "status": "IMPLEMENTED", 
        "classes": ["MainWindow", "FileProcessor"],
        "dependencies": ["logging", "pathlib", "typing", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "config.settings", "config.database", "core.services.calculation_service", "core.services.project_service", "core.repositories.translator_repository", "core.models.project", "core.models.translator", "ui.widgets.file_list_widget", "ui.widgets.calculation_widget", "utils.validation", "utils.logger"],
        "description": "Main application window with splitter layout, file management, calculation display, and full menu system"
    },
    "ui.widgets.file_list_widget": {
        "status": "IMPLEMENTED",
        "classes": ["FileListWidget", "FileItemWidget"],
        "dependencies": ["logging", "typing", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "utils.logger"],
        "description": "Custom widget for managing project files with visual display, selection, and removal capabilities"
    },
    "ui.widgets.calculation_widget": {
        "status": "IMPLEMENTED",
        "classes": ["CalculationWidget", "SummaryPanel", "CategoryBreakdownTable"],
        "dependencies": ["logging", "typing", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "utils.logger", "utils.currency_utils"],
        "description": "Widget for displaying cost calculations with tabbed interface, detailed breakdowns, and summary information"
    },
    "ui.styles.main_style": {
        "status": "IMPLEMENTED",
        "type": "QSS_STYLESHEET",
        "dependencies": ["Qt"],
        "description": "Professional application styling with modern Bootstrap-inspired design"
    },
    
    # Utility Layer
    "utils.logger": {
        "status": "IMPLEMENTED",
        "classes": ["ColoredFormatter", "LogContext"],
        "functions": ["setup_logging", "get_logger", "set_log_level", "add_handler", "remove_handler", "log_exception", "get_log_file_path", "get_log_stats", "cleanup_old_logs"],
        "dependencies": ["logging", "logging.handlers", "os", "pathlib", "typing", "config.settings"],
        "description": "Complete logging setup with file rotation, colored console output, and management utilities"
    },
    "utils.file_utils": {
        "status": "IMPLEMENTED",
        "classes": ["FileUtils", "TempFileManager"],
        "functions": ["get_temp_manager", "ensure_data_directories"],
        "dependencies": ["hashlib", "logging", "mimetypes", "shutil", "pathlib", "typing", "tempfile", "os", "config.settings"],
        "description": "Comprehensive file utilities with temp file management and validation"
    },
    "utils.validation": {
        "status": "IMPLEMENTED",
        "classes": ["ValidationResult", "InputValidator", "FileValidator", "BusinessRuleValidator"],
        "functions": ["validate_input", "validate_file"],
        "dependencies": ["re", "logging", "decimal", "pathlib", "typing", "datetime", "config.settings"],
        "description": "Multi-layer validation system for inputs, files, and business rules"
    },
    "utils.currency_utils": {
        "status": "IMPLEMENTED",
        "classes": ["CurrencyFormatter", "CurrencyConverter", "CostDisplayHelper"],
        "functions": ["format_currency", "format_rate", "parse_currency_input", "get_default_currency"],
        "dependencies": ["logging", "decimal", "typing", "config.settings"],
        "description": "Currency formatting, parsing, and display utilities with internationalization support"
    },
    
    # Database Schema
    "database.schema": {
        "status": "IMPLEMENTED",
        "type": "SQL_SCHEMA",
        "dependencies": ["SQLite"],
        "description": "Complete database schema with tables, indexes, views, and triggers"
    },
    "database.migrations.001_initial": {
        "status": "IMPLEMENTED", 
        "type": "SQL_MIGRATION",
        "dependencies": ["database.schema"],
        "description": "Initial migration with complete schema setup and reference data"
    },
    
    # Application Entry Point
    "main": {
        "status": "IMPLEMENTED",
        "classes": ["TranslationCostCalculator"],
        "functions": ["main"],
        "dependencies": ["sys", "logging", "pathlib", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "config.settings", "config.database", "utils.logger", "ui.main_window"],
        "description": "Main application entry point with initialization and error handling"
    }
}

# =============================================================================
# STUBS (Natural placeholders for future implementation)
# =============================================================================

STUBS = {
    "ui.dialogs.project_dialog": "New project creation dialog (Phase 2)",
    "ui.dialogs.translator_dialog": "Translator management dialog (Phase 2)", 
    "ui.dialogs.rates_dialog": "Rate management dialog (Phase 2)",
    "ui.dialogs.export_dialog": "Export options dialog (Phase 2)",
    "exporters.pdf_exporter": "PDF export functionality (Phase 2)",
    "exporters.excel_exporter": "Excel export functionality (Phase 3)",
    "parsers.phrase_json_parser": "Phrase JSON parser (Phase 3)",
    "parsers.excel_parser": "Excel XLSX parser (Phase 3)",
    "core.services.export_service": "Export coordination service (Phase 2)",
    "utils.currency_utils.CurrencyConverter.convert": "Currency conversion with external API",
    "advanced_rate_management": "Advanced rate import/export features (Phase 2)",
    "ui.main_window.MainWindow.new_project": "New project dialog integration",
    "ui.main_window.MainWindow.open_project": "Project browser dialog",
    "ui.main_window.MainWindow.manage_translators": "Translator management dialog",
    "ui.main_window.MainWindow.manage_clients": "Client management dialog", 
    "ui.main_window.MainWindow.manage_rates": "Rate management dialog",
    "ui.main_window.MainWindow.export_pdf": "PDF export integration"
}

# =============================================================================
# DEPENDENCIES MAP
# =============================================================================

DEPENDENCIES = {
    # External Dependencies
    "PySide6": "GUI framework",
    "PySide6.QtWidgets": "GUI widgets",
    "PySide6.QtCore": "Core Qt functionality",
    "PySide6.QtGui": "GUI elements and styling",
    "sqlite3": "Database (built-in)",
    "dataclasses": "Python built-in",
    "enum": "Python built-in",
    "typing": "Python built-in",
    "decimal": "Python built-in", 
    "datetime": "Python built-in",
    "pathlib": "Python built-in",
    "logging": "Python built-in",
    "sys": "Python built-in",
    "re": "Python built-in",
    "json": "Python built-in",
    "hashlib": "Python built-in",
    "mimetypes": "Python built-in",
    "shutil": "Python built-in",
    "tempfile": "Python built-in",
    "os": "Python built-in",
    "abc": "Python built-in",
    
    # Internal Dependencies (fully implemented interfaces)
    "core.models.match_category.MatchCategoryType": "Enum for match categories",
    "core.models.analysis.FileAnalysisData": "File analysis data container",
    "core.models.analysis.MatchCategoryData": "Individual match category data", 
    "core.models.analysis.ProjectAnalysisData": "Project-level analysis aggregation",
    "core.models.project.Project": "Project domain model",
    "core.models.project.ProjectFile": "Project file model",
    "core.models.translator.Translator": "Translator domain model",
    "core.models.translator.Client": "Client domain model", 
    "core.models.rate.Rate": "Rate model",
    "core.models.rate.LanguagePair": "Language pair model",
    "core.models.rate.RateCalculator": "Rate calculation utilities",
    "core.repositories.base_repository.BaseRepository": "Base repository interface",
    "core.services.calculation_service.CalculationService": "Cost calculation business logic",
    "core.services.project_service.ProjectService": "Project management business logic",
    "ui.widgets.file_list_widget.FileListWidget": "File list management widget",
    "ui.widgets.calculation_widget.CalculationWidget": "Cost calculation display widget",
    "utils.validation.ValidationResult": "Validation result container",
    "utils.file_utils.FileUtils": "File utility functions",
    "utils.currency_utils.CurrencyFormatter": "Currency formatting utilities",
    "utils.logger.get_logger": "Logger factory function"
}

# =============================================================================
# FILES CREATED
# =============================================================================

FILES = [
    "main.py",
    "requirements.txt", 
    "dependency_snapshot.py",
    "config/__init__.py",
    "config/settings.py",
    "config/database.py",
    "core/__init__.py",
    "core/models/__init__.py",
    "core/models/match_category.py",
    "core/models/analysis.py",
    "core/models/project.py", 
    "core/models/translator.py",
    "core/models/rate.py",
    "core/repositories/__init__.py",
    "core/repositories/base_repository.py",
    "core/repositories/project_repository.py",
    "core/repositories/translator_repository.py", 
    "core/repositories/rate_repository.py",
    "core/services/__init__.py",
    "core/services/calculation_service.py",
    "core/services/project_service.py",
    "database/schema.sql",
    "database/migrations/001_initial.sql",
    "parsers/__init__.py",
    "parsers/base_parser.py",
    "parsers/column_detector.py",
    "parsers/trados_csv_parser.py",
    "parsers/parser_factory.py",
    "utils/__init__.py",
    "utils/logger.py",
    "utils/file_utils.py",
    "utils/validation.py",
    "utils/currency_utils.py",
    "ui/__init__.py",
    "ui/main_window.py",  # FULLY IMPLEMENTED
    "ui/widgets/__init__.py",  # NEW
    "ui/widgets/file_list_widget.py",  # NEW
    "ui/widgets/calculation_widget.py",  # NEW
    "ui/styles/main_style.qss"  # NEW
]

# =============================================================================
# NEXT STEPS
# =============================================================================

NEXT_PROMPT = "Phase 2: MVP Development - Advanced UI Dialogs"
NEXT_GOALS = [
    "Implement project creation and management dialogs",
    "Create translator and client management interfaces",
    "Build rate management system with hierarchy support",
    "Add export dialog with PDF generation",
    "Integrate all advanced dialogs with main window",
    "Complete MVP user interface functionality"
]

# =============================================================================
# ARCHITECTURAL NOTES  
# =============================================================================

ARCHITECTURE_NOTES = """
Prompt 5 completes Phase 1 with a fully functional UI framework:

1. MAIN WINDOW: Complete application window with splitter layout, menu system, toolbar, and status bar
2. FILE LIST WIDGET: Custom widget for visual file management with drag/drop support, context menus, and detailed file information
3. CALCULATION WIDGET: Tabbed calculation display with summary panel, category breakdown table, and export preparation
4. PROFESSIONAL STYLING: Modern Bootstrap-inspired QSS stylesheet with consistent colors, typography, and spacing
5. BACKGROUND PROCESSING: Non-blocking file processing with progress indication and error handling
6. SERVICE INTEGRATION: Full integration between UI layer and business services with proper error handling

Key UI features implemented:
- Responsive splitter layout with configurable proportions (30% file list, 70% calculation)
- Project settings bar with translator/client selection and MT percentage configuration
- File list widget with visual file items, CAT tool indicators, word counts, and context menus
- Calculation widget with tabbed interface (Summary, Breakdown, Details)
- Background file processing with progress bar and status updates
- Professional menu bar with File, Edit, View, and Help menus
- Toolbar with quick access to common actions
- Status bar with progress indicator and version display
- Professional styling with modern colors, typography, and consistent spacing

UI Integration highlights:
- Real-time calculation updates when files or settings change
- Visual feedback for all user actions with status messages
- Error handling with user-friendly message dialogs
- Responsive design that works well at different window sizes
- Keyboard shortcuts for common actions (Ctrl+N, Ctrl+O, Ctrl+A, F5, etc.)
- Context-sensitive help and information displays
- Professional file type detection with appropriate icons
- Temporary file support for immediate calculation without project creation

Phase 1 MVP is now complete with a fully functional desktop application that can:
- Load and parse Trados CSV files with intelligent format detection
- Display file information and statistics in an intuitive interface
- Perform cost calculations with configurable MT percentages
- Show detailed calculation breakdowns by match category
- Manage translator and client selection (with stubs for full management)
- Provide professional user experience with modern styling

All expected natural stubs are properly identified for Phase 2 implementation:
- Project creation/management dialogs
- Translator/client/rate management interfaces  
- PDF export functionality
- Advanced calculation features

The UI framework provides a solid foundation for Phase 2 MVP development with advanced dialogs and export capabilities.

PARSER VERIFICATION COMPLETED:
- Column detector correctly identifies 'with_characters' vs 'without_characters' formats
- Word extraction works properly for both CSV format variations  
- Original identical results were due to same project data in different formats
- Parser handles different projects correctly (verified with test data)
- Ready for Phase 2 implementation
"""