#!/usr/bin/env python3
"""
Translation Cost Calculator - Startup Verification

Quick verification script to ensure everything is ready for testing.
Run this before launching main.py
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from scripts/
sys.path.insert(0, str(project_root))

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    required = (3, 11)
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= required:
        print("✅ Python version OK")
        return True
    else:
        print(f"❌ Python {required[0]}.{required[1]}+ required")
        return False

def check_dependencies():
    """Check critical dependencies."""
    dependencies = [
        ('PySide6', 'PySide6.QtWidgets'),
        ('sqlite3', 'sqlite3'),
        ('pathlib', 'pathlib'),
        ('decimal', 'decimal'),
        ('dataclasses', 'dataclasses'),
        ('typing', 'typing')
    ]
    
    print("\nChecking dependencies:")
    all_ok = True
    
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - install with: pip install {name}")
            all_ok = False
    
    return all_ok

def check_file_structure():
    """Check that all required files exist."""
    required_files = [
        'main.py',
        'config/settings.py',
        'config/database.py',
        'core/models/match_category.py',
        'core/models/analysis.py',
        'core/services/calculation_service.py',
        'parsers/trados_csv_parser.py',
        'ui/main_window.py',
        'ui/widgets/file_list_widget.py',
        'ui/widgets/calculation_widget.py',
        'utils/logger.py',
        'database/schema.sql'
    ]
    
    print("\nChecking file structure:")
    all_exist = True
    
    # Change to project root for file checking
    os.chdir(project_root)
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist

def check_csv_test_files():
    """Check for CSV test files in test_data folder."""
    # Look in test_data folder
    test_data_dir = project_root / "test_data"
    
    csv_files = [
        'csv_Analysis_example_1.csv',
        'csv_Analysis_example_2.csv'
    ]
    
    txt_files = [
        'csv_Analysis_example_1.txt',
        'csv_Analysis_example_2.txt'
    ]
    
    print(f"\nChecking test files in: {test_data_dir}")
    
    # Create test_data directory if it doesn't exist
    if not test_data_dir.exists():
        print(f"📁 Creating test_data directory...")
        test_data_dir.mkdir(exist_ok=True)
    
    files_found = 0
    
    for csv_file, txt_file in zip(csv_files, txt_files):
        csv_path = test_data_dir / csv_file
        txt_path = test_data_dir / txt_file
        
        # Also check root directory for files that might be misplaced
        root_csv_path = project_root / csv_file
        root_txt_path = project_root / txt_file
        
        if csv_path.exists():
            print(f"✅ {csv_file} found in test_data/")
            files_found += 1
        elif txt_path.exists():
            print(f"💡 {txt_file} found in test_data/ - rename to {csv_file}")
            # Auto-rename if possible
            try:
                txt_path.rename(csv_path)
                print(f"✅ Renamed to {csv_file}")
                files_found += 1
            except Exception as e:
                print(f"❌ Could not rename: {e}")
        elif root_csv_path.exists():
            print(f"💡 {csv_file} found in root - moving to test_data/")
            try:
                root_csv_path.rename(csv_path)
                print(f"✅ Moved to test_data/{csv_file}")
                files_found += 1
            except Exception as e:
                print(f"❌ Could not move: {e}")
        elif root_txt_path.exists():
            print(f"💡 {txt_file} found in root - moving and renaming to test_data/")
            try:
                root_txt_path.rename(csv_path)
                print(f"✅ Moved and renamed to test_data/{csv_file}")
                files_found += 1
            except Exception as e:
                print(f"❌ Could not move: {e}")
        else:
            print(f"❌ {csv_file} not found anywhere")
    
    if files_found == len(csv_files):
        print("✅ All test files ready!")
        return True
    else:
        print(f"⚠️  {files_found}/{len(csv_files)} test files found")
        return files_found > 0

def test_basic_imports():
    """Test basic imports to catch issues early."""
    print("\nTesting critical imports:")
    
    test_imports = [
        ('config.settings', 'Settings'),
        ('parsers.trados_csv_parser', 'TradosCSVParser'),
        ('core.models.analysis', 'FileAnalysisData'),
        ('utils.logger', 'setup_logging')
    ]
    
    all_ok = True
    
    for module, item in test_imports:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"✅ {module}.{item}")
        except Exception as e:
            print(f"❌ {module}.{item}: {e}")
            all_ok = False
    
    return all_ok

def create_directories():
    """Create required directories."""
    directories = [
        'data',
        'logs',
        'assets',
        'test_data'
    ]
    
    print("\nCreating directories:")
    
    for directory in directories:
        try:
            dir_path = project_root / directory
            dir_path.mkdir(exist_ok=True)
            print(f"✅ {directory}/")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")

def main():
    """Main verification function."""
    print("🔍 Translation Cost Calculator - Startup Verification")
    print(f"📁 Project root: {project_root}")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Basic Imports", test_basic_imports)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} check failed")
    
    # Always run these
    check_csv_test_files()
    create_directories()
    
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {passed}/{total} critical checks passed")
    
    if passed == total:
        print("✅ All critical checks passed!")
        print("\n🚀 Ready to launch:")
        print("   python main.py")
        print("\n🧪 Or run tests first:")
        print("   python scripts/testing_script.py")
        return True
    else:
        print("❌ Some critical checks failed")
        print("\n🔧 Fix the issues above, then try again")
        return False

if __name__ == "__main__":
    success = main()
    input(f"\nPress Enter to {'launch the application' if success else 'exit'}...")
    
    if success:
        # Launch main application from project root
        try:
            os.chdir(project_root)
            import main
            sys.exit(main.main())
        except Exception as e:
            print(f"❌ Launch failed: {e}")
            sys.exit(1)
    else:
        sys.exit(1)