# Translation Cost Calculator - Project Bible v2.1

## Project Overview

**Project Name**: Desktop Translation Cost Calculator  
**Technology Stack**: Python 3.11+, PySide6, SQLite, PyInstaller  
**Platform**: Windows 10+  
**Target Users**: 5-10 Project Managers  
**Development Language**: English (code, comments, documentation)

## Architecture Philosophy

**Clean Architecture** with clear layer separation:
- **Domain Layer**: Core business logic (models, services)
- **Data Layer**: Repositories, database access  
- **Application Layer**: Use cases, application services
- **Presentation Layer**: UI components, dialogs
- **Infrastructure Layer**: File parsers, exporters, external dependencies

**Design Principles**:
- SOLID principles throughout
- Dependency injection for testability
- Plugin architecture for extensibility
- Repository pattern for data access
- Command pattern for complex operations

## Code Quality Standards

### 1. Code Style
- **Language**: English for all code, comments, documentation
- **Type Hints**: Required for all public methods and properties
- **Docstrings**: Required for all classes and public methods
- **PEP 8**: Strict compliance
- **Naming**: Clear, descriptive names (no abbreviations unless standard)

### 2. Error Handling
- **Specific Exceptions**: Custom exception types for different error scenarios
- **User-Friendly Messages**: Clear error messages in UI layer
- **Comprehensive Logging**: Debug info without sensitive data
- **Graceful Degradation**: Fallback behavior when possible

### 3. Performance Requirements
- **Startup Time**: < 3 seconds on target hardware
- **File Parsing**: < 5 seconds for typical CAT analysis files
- **UI Responsiveness**: No blocking operations in main thread
- **Memory Usage**: < 100MB for typical project workloads

### 4. Testing Standards
- **Unit Tests**: 90%+ coverage for business logic
- **Parser Tests**: 100% coverage with real file samples
- **Integration Tests**: Complete CRUD cycles for repositories
- **UI Tests**: Critical user workflows

## Project Structure

```
translation_calculator/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── dependency_snapshot.py           # Project state tracking
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Application configuration
│   └── database.py                  # Database configuration
├── core/                           # Business logic layer
│   ├── __init__.py
│   ├── models/                     # Domain models
│   │   ├── __init__.py
│   │   ├── project.py              # Project domain model
│   │   ├── translator.py           # Translator domain model
│   │   ├── rate.py                 # Rate system model
│   │   ├── analysis.py             # File analysis model
│   │   └── match_category.py       # Match categories enum
│   ├── services/                   # Business services
│   │   ├── __init__.py
│   │   ├── project_service.py      # Project management service
│   │   ├── translator_service.py   # Translator management service
│   │   ├── rate_service.py         # Rate management service
│   │   ├── calculation_service.py  # Cost calculation service
│   │   └── export_service.py       # Export coordination service
│   └── repositories/               # Data access layer
│       ├── __init__.py
│       ├── base_repository.py      # Base repository interface
│       ├── project_repository.py   # Project data access
│       ├── translator_repository.py # Translator data access
│       └── rate_repository.py      # Rate data access
├── parsers/                        # CAT file parsers layer
│   ├── __init__.py
│   ├── base_parser.py              # Parser interface
│   ├── trados_csv_parser.py        # Trados CSV parser
│   ├── phrase_json_parser.py       # Phrase JSON parser (Phase 3)
│   ├── excel_parser.py             # Excel XLSX parser (Phase 3)
│   ├── column_detector.py          # Intelligent column detection
│   └── parser_factory.py           # Parser factory
├── exporters/                      # Report exporters layer
│   ├── __init__.py
│   ├── base_exporter.py            # Exporter interface
│   ├── pdf_exporter.py             # PDF report exporter
│   └── excel_exporter.py           # Excel report exporter (Phase 3)
├── ui/                             # Presentation layer
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── dialogs/                    # Dialog windows
│   │   ├── __init__.py
│   │   ├── project_dialog.py       # New project dialog
│   │   ├── translator_dialog.py    # Translator management dialog
│   │   ├── rates_dialog.py         # Rate management dialog
│   │   ├── column_mapping_dialog.py # Column mapping (Phase 3)
│   │   └── export_dialog.py        # Export options dialog
│   ├── widgets/                    # Custom widgets
│   │   ├── __init__.py
│   │   ├── file_list_widget.py     # File list management widget
│   │   ├── rate_table_widget.py    # Rate table widget
│   │   └── calculation_widget.py   # Cost calculation display widget
│   └── styles/                     # UI styling
│       ├── __init__.py
│       └── main_style.qss          # Application stylesheet
├── database/                       # Database layer
│   ├── __init__.py
│   ├── migrations/                 # Database migrations
│   │   ├── __init__.py
│   │   └── 001_initial.sql         # Initial database schema
│   └── schema.sql                  # Current database schema
├── utils/                          # Utility layer
│   ├── __init__.py
│   ├── logger.py                   # Logging configuration
│   ├── file_utils.py               # File handling utilities
│   ├── currency_utils.py           # Currency formatting utilities
│   └── validation.py               # Input validation utilities
└── tests/                          # Testing layer
    ├── __init__.py
    ├── test_parsers/               # Parser tests
    ├── test_services/              # Service tests
    └── test_ui/                    # UI tests
```

## Business Domain Models

### Match Category System
```python
class MatchCategoryType(Enum):
    CONTEXT_MATCH = "Context Match"     # 0.03 EUR/word (typical)
    REPETITIONS = "Repetitions"         # 0.03 EUR/word (typical)
    EXACT_MATCH = "100%"               # 0.05 EUR/word (typical)
    HIGH_FUZZY = "95% - 99%"           # 0.08 EUR/word (typical)
    MEDIUM_HIGH_FUZZY = "85% - 94%"    # 0.10 EUR/word (typical)
    MEDIUM_FUZZY = "75% - 84%"         # 0.11 EUR/word (typical)
    LOW_FUZZY = "50% - 74%"            # 0.12 EUR/word (typical)
    NO_MATCH = "No Match"              # 0.12 EUR/word (typical)
    MT_MATCH = "MT Match"              # 0.02 EUR/word (typical)
    
    # Phrase JSON mapping utility
    @classmethod
    def from_phrase_key(cls, phrase_key: str) -> 'MatchCategoryType':
        mapping = {
            'contextMatch': cls.CONTEXT_MATCH,
            'repetitions': cls.REPETITIONS,
            'match100': cls.EXACT_MATCH,
            'match95': cls.HIGH_FUZZY,
            'match85': cls.MEDIUM_HIGH_FUZZY, 
            'match75': cls.MEDIUM_FUZZY,
            'match50': cls.LOW_FUZZY,
            'match0': cls.NO_MATCH
        }
        return mapping.get(phrase_key, cls.NO_MATCH)
```

### MT Percentage Logic
- Applied only to 100% matches
- Default: 70% MT, 30% TM
- MT matches get lower rate than TM matches
- User configurable per project

### Rate Hierarchy
1. **Client-specific rates** (highest priority)
2. **General translator rates** (fallback)
3. **Default rates** (system fallback)
4. **Minimum fee** (per translator/client combination)

### Calculation Formula
```
Total Cost = Σ(Category Words × Category Rate) 
Final Cost = max(Total Cost, Minimum Fee)
```

## File Format Specifications

### Trados CSV Format
- **Headers**: Two-line header system with category blocks
- **Delimiter**: Semicolon (;)
- **Encoding**: UTF-8 with BOM support
- **File info**: "filename | source_lang>target_lang" format
- **Format Variations**:
  - **Type 1**: 5 semicolons between categories (includes Characters column per category)
  - **Type 2**: 4 semicolons between categories (no Characters column per category)
- **Standard columns per category**: Segments, Words, Placeables, Percent
- **Optional column**: Characters (varies by export settings)
- **Categories**: Context Match, Repetitions, 100%, 95%-99%, 85%-94%, 75%-84%, 50%-74%, No Match, Total

### Phrase JSON Format (Phase 3)
- **Structure**: Hierarchical JSON: `projectName` → `analyseLanguageParts` → `jobs` (individual files)
- **Match categories**: `contextMatch`, `repetitions`, `match100`, `match95`, `match85`, `match75`, `match50`, `match0`
- **Special match100 structure**: Contains `{sum, tm, mt, nt}` breakdown for TM/MT separation
- **Data fields**: segments, words, characters, normalizedPages, percent, editingTime
- **Language pair**: Stored as `sourceLang` and `targetLang` properties
- **Multi-file support**: Single JSON can contain multiple files in `jobs` array

### Excel XLSX Format (Phase 3)
- **Structure**: Various layouts depending on CAT tool
- **Detection**: Column header pattern matching
- **Encoding**: Native Excel encoding
- **Required fields**: Configurable through mapping dialog

## Database Schema

### Core Tables
```sql
-- Translators
CREATE TABLE translators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clients
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Language Pairs
CREATE TABLE language_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    UNIQUE(source_language, target_language)
);

-- Match Categories
CREATE TABLE match_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_order INTEGER NOT NULL
);

-- Translator Rates
CREATE TABLE translator_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translator_id INTEGER NOT NULL,
    client_id INTEGER NULL,
    language_pair_id INTEGER NOT NULL,
    match_category_id INTEGER NOT NULL,
    rate_per_word DECIMAL(10,4) NOT NULL,
    minimum_fee DECIMAL(10,2) DEFAULT 0,
    is_minimum_fee_enabled BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (translator_id) REFERENCES translators(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id),
    FOREIGN KEY (match_category_id) REFERENCES match_categories(id),
    UNIQUE(translator_id, client_id, language_pair_id, match_category_id)
);

-- Projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    translator_id INTEGER NOT NULL,
    client_id INTEGER,
    language_pair_id INTEGER NOT NULL,
    mt_percentage INTEGER DEFAULT 70,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (translator_id) REFERENCES translators(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id)
);

-- Project Files
CREATE TABLE project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    parsed_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

## UI/UX Requirements

### Main Window Layout
- **Left Panel**: Project file list (30% width)
- **Right Panel**: Calculation results (70% width)
- **Toolbar**: Quick action buttons
- **Status Bar**: Operation feedback
- **Menu Bar**: Full feature access

### Dialog Standards
- **Modal dialogs** for data entry
- **Input validation** with user feedback
- **Cancel/OK** button pattern
- **Keyboard shortcuts** for power users
- **Tab order** optimization

### Visual Design
- **Professional appearance** suitable for business use
- **Clear typography** with readable fonts
- **Consistent spacing** and alignment
- **Color coding** for different match categories
- **Icons** for common actions

## Export Requirements

### PDF Export
- **Professional layout** with company branding
- **Project information** header
- **Cost breakdown** by match categories
- **File breakdown** for multi-file projects
- **Total cost** prominently displayed
- **Date and translator** information

### Excel Export (Phase 3)
- **Structured data** for further analysis
- **Multiple sheets** (summary, detailed breakdown)
- **Formulas** for verification
- **Formatting** for readability
- **Charts** for visual representation

## Deployment Requirements

### Build Process
- **PyInstaller** for executable creation
- **One-file** distribution for simplicity
- **Windows executable** with proper icon
- **Dependency bundling** for offline operation

### Installation Requirements
- **Windows 10+** compatibility
- **No admin rights** required for installation
- **Portable mode** support
- **Automatic updates** consideration (future)

## Security Considerations

### Data Protection
- **Local data storage** only (SQLite)
- **No cloud dependencies** for core functionality
- **Input sanitization** for all user inputs
- **File type validation** for uploads

### Error Handling
- **No sensitive data** in error messages
- **Graceful failure** modes
- **User-friendly** error reporting
- **Debug logging** without sensitive data

---

**Document Version**: 2.1  
**Last Updated**: 2025-01-04  
**Next Review**: Phase 1 Completion