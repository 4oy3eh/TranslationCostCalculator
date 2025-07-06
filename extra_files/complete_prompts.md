# Translation Cost Calculator - Prompt Collection v2.1

## Dependency Management Instructions

### For User:
1. **Before Each Prompt**: Attach `dependency_snapshot.py` (always current version)
2. **Additional Files**: Attach only if specified in "Required Files" section  
3. **After Each Prompt**: Update `dependency_snapshot.py` with provided changes
4. **Stub Replacements**: Use separate prompts when indicated

### For Claude:
1. Every response MUST end with "Self-Check" + "Dependency Snapshot Update" sections
2. Natural stubs are OK - track them in STUBS section
3. Provide exact code blocks for snapshot updates
4. Keep interfaces minimal for token efficiency
5. Update FILES tracking with created file list
6. Follow mandatory response format from Project Bible
7. Always verify component dependencies before using them

---

## Phase 1: Core Infrastructure (Prompts 1-5)

### Prompt 1: Project Structure & Core Models
**Context**: Translation Cost Calculator project initialization  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Basic project structure and core domain models  
**Required Files**: None (fresh start)  
**Goal**: Create complete project folder structure, configuration, and domain models  
**Files to Create**:
- `main.py` - Application entry point
- `requirements.txt` - Python dependencies  
- `dependency_snapshot.py` - Initial dependency tracker
- `config/settings.py` - Application configuration
- `config/database.py` - Database configuration
- `core/models/match_category.py` - Match category enum with Phrase mapping
- `core/models/analysis.py` - File analysis model with TM/MT support
- `core/models/project.py` - Project domain model
- `core/models/translator.py` - Translator domain model
- `core/models/rate.py` - Rate system model
**Expected Natural Stubs**: Database connection methods, complex UI dialogs

**Response Format**: Must follow mandatory format from Project Bible including Self-Check section

---

### Prompt 2: Database Layer & Repositories  
**Context**: Translation Cost Calculator data persistence layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: SQLite database schema and repository pattern implementation  
**Required Files**: `dependency_snapshot.py` + files from Prompt 1  
**Goal**: Complete database schema with migrations and basic repository pattern  
**Files to Create**:
- `database/schema.sql` - Complete database schema
- `database/migrations/001_initial.sql` - Initial migration
- `core/repositories/base_repository.py` - Base repository interface
- `core/repositories/project_repository.py` - Project data access
- `core/repositories/translator_repository.py` - Translator data access  
- `core/repositories/rate_repository.py` - Rate data access
**Expected Natural Stubs**: Complex query operations, data validation

**Response Format**: Must follow mandatory format from Project Bible

---

### Prompt 3: Trados CSV Parser & Column Detection
**Context**: Translation Cost Calculator file parsing layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Intelligent Trados CSV parser with format detection  
**Required Files**: 
- `dependency_snapshot.py` + all previous files
- `csv_Analysis_example_1.csv` (5 semicolon format)
- `csv_Analysis_example_2.csv` (4 semicolon format)
**Goal**: Parse both Trados CSV format variations with intelligent column detection  
**Files to Create**:
- `parsers/base_parser.py` - Parser interface
- `parsers/trados_csv_parser.py` - Complete Trados CSV parser
- `parsers/column_detector.py` - Intelligent column detection for both formats
- `parsers/parser_factory.py` - Parser factory (Phase 1 version)
- `utils/file_utils.py` - File handling utilities
- `utils/validation.py` - Input validation utilities  
**Expected Natural Stubs**: JSON/Excel parsers (Phase 3), advanced validation

---

### Prompt 4: Business Services & Calculation Logic
**Context**: Translation Cost Calculator business logic layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Cost calculation and project management services  
**Required Files**: `dependency_snapshot.py` + all previous files  
**Goal**: Implement core business logic for cost calculation and project management  
**Files to Create**:
- `core/services/calculation_service.py` - Cost calculation with MT percentage logic
- `core/services/project_service.py` - Project creation and management
- `utils/currency_utils.py` - Currency formatting utilities
- `utils/logger.py` - Logging configuration
**Expected Natural Stubs**: Advanced rate management, export services, UI integration

---

### Prompt 5: Basic UI Framework & Main Window
**Context**: Translation Cost Calculator user interface layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Main application window with basic file handling and calculation display  
**Required Files**: `dependency_snapshot.py` + all previous files  
**Goal**: Functional UI for file loading, parsing, and calculation display  
**Files to Create**:
- `ui/main_window.py` - Main application window with splitter layout
- `ui/widgets/file_list_widget.py` - File list management widget  
- `ui/widgets/calculation_widget.py` - Cost calculation display widget
- `ui/styles/main_style.qss` - Basic application styling
**Expected Natural Stubs**: Advanced dialogs, rate management UI, export dialogs

---

## Phase 2: MVP Development (Prompts 6-13)

### Prompt 6: Advanced UI Dialogs
**Context**: Translation Cost Calculator dialog system  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Replace basic dialogs with full-featured forms  
**Required Files**: `dependency_snapshot.py` + all Phase 1 files  
**Goal**: Professional dialog system for project, translator, and rate management  
**Files to Create**:
- `ui/dialogs/project_dialog.py` - New project creation dialog
- `ui/dialogs/translator_dialog.py` - Translator management dialog
- `ui/dialogs/rates_dialog.py` - Rate management dialog
- `ui/dialogs/export_dialog.py` - Export options dialog
**Expected Natural Stubs**: None (replaces existing stubs)

---

### Prompt 7: Advanced Rate Management System
**Context**: Translation Cost Calculator rate system  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Client-specific rates with minimum fees and rate hierarchy  
**Required Files**: All previous files  
**Goal**: Complete rate management with client-specific rates and minimum fees  
**Files to Create**:
- `core/services/rate_service.py` - Advanced rate management with hierarchy
- `ui/widgets/rate_table_widget.py` - Rate table widget with editing
**Expected Natural Stubs**: Rate import/export functionality

---

### Prompt 8: PDF Export System  
**Context**: Translation Cost Calculator export layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Professional PDF report generation  
**Required Files**: All previous files  
**Goal**: Generate professional PDF quotes with project breakdown  
**Files to Create**:
- `exporters/base_exporter.py` - Exporter interface
- `exporters/pdf_exporter.py` - PDF report generation with ReportLab
- `core/services/export_service.py` - Export coordination service
**Expected Natural Stubs**: Excel export (Phase 3), advanced formatting options

---

### Prompt 9: Data Import/Export Features
**Context**: Translation Cost Calculator data management  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Import/export functionality for translators and rates  
**Required Files**: All previous files  
**Goal**: CSV/Excel import/export for translator and rate data  
**Files to Create**:
- `core/services/translator_service.py` - Translator management with import/export
- Enhanced rate_service.py with import/export capabilities
**Expected Natural Stubs**: Advanced data validation, batch operations

---

### Prompt 10: Enhanced UI Integration  
**Context**: Translation Cost Calculator UI completion  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Complete UI integration with all services  
**Required Files**: All previous files  
**Goal**: Fully integrated UI with all functionality working  
**Files to Create**:
- Enhanced main_window.py with full menu system
- Integration of all dialogs and widgets
**Expected Natural Stubs**: None (completes basic UI)

---

### Prompt 11: Testing & Validation Framework
**Context**: Translation Cost Calculator testing layer  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Comprehensive testing suite  
**Required Files**: All previous files  
**Goal**: Unit and integration tests for core functionality  
**Files to Create**:
- `tests/test_parsers/test_trados_parser.py` - CSV parser tests
- `tests/test_services/test_calculation_service.py` - Calculation logic tests  
- `tests/test_ui/test_main_window.py` - Basic UI tests
**Expected Natural Stubs**: Performance tests, UI automation tests

---

### Prompt 12: Application Packaging & Build
**Context**: Translation Cost Calculator deployment  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: PyInstaller setup and executable creation  
**Required Files**: All implemented files  
**Goal**: Package application into Windows executable  
**Files to Create**:
- `build_spec.py` - PyInstaller specification
- `build.bat` - Build script
- `assets/icon.ico` - Application icon
**Expected Natural Stubs**: Auto-update system, installer creation

---

### Prompt 13: MVP Integration & Final Testing
**Context**: Translation Cost Calculator MVP completion  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Final integration and end-to-end testing  
**Required Files**: All implemented files  
**Goal**: Complete, tested, packaged MVP application  
**Files to Create**:
- Integration fixes and final testing
- Documentation updates
**Expected Natural Stubs**: None (MVP complete)

---

## Phase 3: Full Version (Prompts 14-19)

### Prompt 14: Phrase JSON Parser
**Context**: Translation Cost Calculator multi-format support  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Phrase CAT tool JSON support with TM/MT breakdown  
**Required Files**: 
- All MVP files
- `json_Analysis_example_1.json` (Phrase JSON sample)
**Goal**: Parse Phrase JSON format with proper TM/MT handling  
**Files to Create**:
- `parsers/phrase_json_parser.py` - Complete Phrase JSON parser
**Expected Natural Stubs**: None (specific parser implementation)

---

### Prompt 15: Excel XLSX Parser
**Context**: Translation Cost Calculator Excel support  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Excel CAT analysis file support  
**Required Files**: 
- All previous files  
- Excel sample files (to be provided)
**Goal**: Parse Excel CAT analysis files with configurable mapping  
**Files to Create**:
- `parsers/excel_parser.py` - Excel XLSX parser
**Expected Natural Stubs**: Advanced Excel features, complex mapping

---

### Prompt 16: Column Mapping Dialog
**Context**: Translation Cost Calculator manual mapping support  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Manual column mapping for unknown formats  
**Required Files**: All previous files  
**Goal**: User interface for manual column mapping when auto-detection fails  
**Files to Create**:
- `ui/dialogs/column_mapping_dialog.py` - Interactive column mapping dialog
**Expected Natural Stubs**: None (specific UI component)

---

### Prompt 17: Advanced Export Features  
**Context**: Translation Cost Calculator enhanced export  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Excel export and enhanced PDF features  
**Required Files**: All previous files  
**Goal**: Advanced export capabilities with Excel and enhanced PDF  
**Files to Create**:
- `exporters/excel_exporter.py` - Excel export with charts and formulas
- Enhanced PDF exporter with company branding
**Expected Natural Stubs**: None (completes export system)

---

### Prompt 18: Enhanced UI/UX & Polish
**Context**: Translation Cost Calculator UI enhancement  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: UI polish and advanced features  
**Required Files**: All previous files  
**Goal**: Enhanced user experience with advanced UI features  
**Files to Create**:
- Enhanced styling and visual improvements
- Advanced UI features and shortcuts
**Expected Natural Stubs**: None (UI polish)

---

### Prompt 19: Final Integration & Documentation
**Context**: Translation Cost Calculator project completion  
**Bible**: [Attached: projectBible.md v2.1]  
**Component**: Final integration, testing, and documentation  
**Required Files**: All implemented files  
**Goal**: Complete, tested, documented application  
**Files to Create**:
- Final integration and testing
- User documentation
- Developer documentation
**Expected Natural Stubs**: None (project complete)

---

## Required Sample Files

### Phase 1:
- `csv_Analysis_example_1.csv` - Trados CSV with Characters (5 semicolons)
- `csv_Analysis_example_2.csv` - Trados CSV without Characters (4 semicolons)

### Phase 3:  
- `json_Analysis_example_1.json` - Phrase JSON with TM/MT breakdown
- Excel sample files (to be provided when needed)

---

**Collection Version**: 2.1  
**Last Updated**: 2025-01-04  
**Total Prompts**: 19