# dependency_snapshot.py
# Translation Cost Calculator - Dependency Snapshot v2.2
# Tracks project status with phase-based component tracking
# Version: 0.0 | Status: Initial - no components implemented
# Last Update: Initial creation

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Phase-based Component Status (True = completed, False = pending)
COMPONENT_STATUS = {
    "phase_1_core": {
        "project_structure": False,     # Prompt 1 - Foundation setup
        "database_layer": False,        # Prompt 2 - SQLite + repositories  
        "trados_parser": False,         # Prompt 3 - CSV parsing + column detection
        "business_services": False,     # Prompt 4 - Calculation + project services
        "basic_ui": False,             # Prompt 5 - Main window + widgets
    },
    "phase_2_mvp": {
        "advanced_dialogs": False,      # Prompt 6 - UI dialogs
        "rate_management": False,       # Prompt 7 - Advanced rate system
        "pdf_export": False,           # Prompt 8 - PDF generation
        "data_import_export": False,   # Prompt 9 - CSV/Excel import/export
        "ui_integration": False,       # Prompt 10 - Complete UI
        "testing_framework": False,    # Prompt 11 - Test suite
        "application_packaging": False, # Prompt 12 - PyInstaller
        "mvp_integration": False,      # Prompt 13 - Final MVP
    },
    "phase_3_full": {
        "phrase_parser": False,        # Prompt 14 - JSON parsing
        "excel_parser": False,         # Prompt 15 - Excel parsing
        "column_mapping": False,       # Prompt 16 - Manual mapping UI
        "advanced_export": False,      # Prompt 17 - Excel export
        "enhanced_ui": False,         # Prompt 18 - UI polish
        "final_integration": False,    # Prompt 19 - Final testing
    }
}

# Minimal Interface Definitions (for token efficiency)
class I:
    """Compact interface definitions for implemented components"""
    
    # Phase 1 Interfaces (will be added as components are implemented)
    class MatchCategoryType:
        """Enum for translation match categories with Phrase mapping"""
        from_phrase_key: callable  # static method
        
    class MatchCategory:
        """Match category data with TM/MT support"""
        type: object
        words: float
        segments: int
        characters: int
        tm_words: float  # TM-specific for 100% matches
        mt_words: float  # MT-specific for 100% matches
        
    class FileAnalysis:
        """Parsed CAT analysis file data"""
        filename: str
        source_language: str
        target_language: str
        categories: dict
        total_words: float
        get_adjusted_categories: callable  # Apply MT percentage
        
    class TradosCSVParser:
        """Trados CSV parser with format detection"""
        can_parse: callable  # static
        parse: callable
        get_supported_extensions: callable
        
    class ColumnDetector:
        """Intelligent column detection for CSV variations"""
        detect_trados_columns: callable
        
    class CalculationService:
        """Cost calculation with rate hierarchy"""
        calculate_project_cost: callable
        
    class ProjectService:
        """Project management operations"""
        create_project: callable
        add_files_to_project: callable
        
    # Phase 2 Interfaces (stubs for now)
    class RateService:
        """STUB: Advanced rate management with client-specific rates"""
        get_rate_hierarchy: callable  # STUB - Prompt 7
        
    class PDFExporter:
        """STUB: Professional PDF generation"""
        export: callable  # STUB - Prompt 8
        
    # Phase 3 Interfaces (stubs for now)
    class PhraseJSONParser:
        """STUB: Phrase JSON parser with TM/MT breakdown"""
        parse: callable  # STUB - Prompt 14
        
    class ExcelParser:
        """STUB: Excel XLSX parser"""
        parse: callable  # STUB - Prompt 15

# Files Created by Prompt (updated after each completion)
FILES = {
    "prompt_1": [],  # Will be populated: main.py, requirements.txt, config/, core/models/
    "prompt_2": [],  # Will be populated: database/, core/repositories/
    "prompt_3": [],  # Will be populated: parsers/, utils/
    "prompt_4": [],  # Will be populated: core/services/
    "prompt_5": [],  # Will be populated: ui/, ui/widgets/
    # ... continues for all prompts
}

# Stub Tracking (Natural stubs to be replaced later)
STUBS = {
    # Phase 1 → Phase 2 replacements
    "basic_dialogs": {
        "created": "Prompt 5", 
        "implement": "Prompt 6", 
        "location": "ui/main_window.py",
        "description": "QInputDialog placeholders for project creation"
    },
    "simple_rate_lookup": {
        "created": "Prompt 4",
        "implement": "Prompt 7", 
        "location": "core/services/calculation_service.py",
        "description": "Basic rate retrieval without client-specific logic"
    },
    "basic_export": {
        "created": "Prompt 5",
        "implement": "Prompt 8",
        "location": "ui/main_window.py", 
        "description": "Simple text file output instead of PDF"
    },
    
    # Phase 2 → Phase 3 replacements  
    "single_parser_factory": {
        "created": "Prompt 3",
        "implement": "Prompt 14",
        "location": "parsers/parser_factory.py",
        "description": "Only supports Trados CSV"
    },
    "basic_pdf_export": {
        "created": "Prompt 8", 
        "implement": "Prompt 17",
        "location": "exporters/pdf_exporter.py",
        "description": "Simple PDF without advanced formatting"
    }
}

# Required Sample Files
SAMPLE_FILES = {
    "phase_1": [
        "csv_Analysis_example_1.csv",  # 5 semicolon format
        "csv_Analysis_example_2.csv"   # 4 semicolon format
    ],
    "phase_3": [
        "json_Analysis_example_1.json", # Phrase JSON with TM/MT
        "excel_sample.xlsx"              # To be provided
    ]
}

# Quick Status Functions
def get_phase_progress() -> Dict[str, str]:
    """Get completion status for each phase"""
    progress = {}
    for phase, components in COMPONENT_STATUS.items():
        completed = sum(1 for c in components.values() if c)
        total = len(components)
        progress[phase] = f"{completed}/{total}"
    return progress

def get_current_prompt() -> int:
    """Get next prompt number based on completion status"""
    all_components = []
    for phase in COMPONENT_STATUS.values():
        all_components.extend(phase.values())
    return sum(1 for c in all_components if c) + 1

def get_ready_components() -> List[str]:
    """Get list of completed components ready for use"""
    ready = []
    for phase_name, components in COMPONENT_STATUS.items():
        for component, is_complete in components.items():
            if is_complete:
                ready.append(f"{phase_name}.{component}")
    return ready

def get_active_stubs() -> List[str]:
    """Get stubs that should be addressed in upcoming prompts"""
    current_prompt = get_current_prompt()
    active = []
    for stub_name, stub_info in STUBS.items():
        implement_prompt = int(stub_info["implement"].split(" ")[1])
        if implement_prompt <= current_prompt + 2:  # Next 2 prompts
            active.append(stub_name)
    return active

def mark_component_complete(component_name: str) -> bool:
    """Mark a component as completed"""
    for phase, components in COMPONENT_STATUS.items():
        if component_name in components:
            components[component_name] = True
            return True
    return False

def remove_stub(stub_name: str) -> None:
    """Remove stub when it's been replaced"""
    if stub_name in STUBS:
        del STUBS[stub_name]

def add_interface(component_name: str, interface_definition: str) -> None:
    """Add new interface definition to class I"""
    # This would dynamically add to the I class
    # Implementation details handled in actual updates

def get_mandatory_response_format() -> str:
    """Get the mandatory response format for prompts"""
    return """
## Dependency Snapshot Update

**Component Status:**
```python
mark_component_complete("component_name")
```

**Files Created:**
```python
add_files("X", [
    "file1.py",
    "file2.py"
])
```

**Interface Updates:**
```python
# Add to class I
class NewComponent:
    method_name: callable
```

**Stubs Added/Removed:**
```python
# Add/remove stubs as needed
```
"""

# Phase Completion Checklists
PHASE_CHECKLISTS = {
    "phase_1": [
        "Project structure with proper package layout",
        "Core models with type hints and validation", 
        "SQLite database with complete schema",
        "Trados CSV parser handles both format variations",
        "Basic calculation logic with MT percentage",
        "Main UI window shows files and calculation results"
    ],
    "phase_2": [
        "Professional UI dialogs for all operations",
        "Client-specific rate management system",
        "PDF export with professional formatting",
        "CSV/Excel import/export for translator data",
        "Complete UI integration with all features",
        "Comprehensive test suite with good coverage",
        "PyInstaller executable generation",
        "End-to-end MVP functionality"
    ],
    "phase_3": [
        "Phrase JSON parser with TM/MT breakdown",
        "Excel XLSX parser with flexible mapping", 
        "Manual column mapping dialog interface",
        "Advanced export with Excel and enhanced PDF",
        "Polished UI with enhanced user experience",
        "Complete documentation and final testing"
    ]
}

if __name__ == "__main__":
    print("Translation Cost Calculator - Dependency Status")
    print("=" * 55)
    print(f"Current Prompt: {get_current_prompt()}")
    print()
    for phase, progress in get_phase_progress().items():
        completed_count = int(progress.split('/')[0])
        total_count = int(progress.split('/')[1])
        percentage = (completed_count / total_count * 100) if total_count > 0 else 0
        print(f"{phase}: {progress} ({percentage:.0f}%)")
    
    ready = get_ready_components()
    if ready:
        print(f"\nReady components: {len(ready)}")
        for component in ready:
            print(f"  ✓ {component}")
    
    active_stubs = get_active_stubs()
    if active_stubs:
        print(f"\nActive stubs to address:")
        for stub in active_stubs:
            print(f"  ⚠ {stub} (→ {STUBS[stub]['implement']})")