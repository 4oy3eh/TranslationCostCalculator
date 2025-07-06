"""
Translation Cost Calculator - Startup Check

Quick startup validation to ensure the application can run properly.
"""

import sys
import os
from pathlib import Path

def check_and_fix_imports():
    """Check and fix import path issues."""
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print(f"Project root: {project_root}")
    print(f"Python path updated: {str(project_root) in sys.path}")
    
    # Check PySide6 availability
    try:
        import PySide6
        from PySide6 import QtWidgets, QtCore, QtGui
        print("✅ PySide6 imports successful")
        return True
    except ImportError as e:
        print(f"❌ PySide6 import failed: {e}")
        print("💡 Install with: pip install PySide6")
        return False

def create_required_directories():
    """Create required directories if they don't exist."""
    
    directories = [
        "data",
        "logs", 
        "assets",
        "database",
        "database/migrations",
        "ui/styles"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created/verified: {dir_path}/")

def test_basic_imports():
    """Test basic project imports."""
    
    try:
        # Test configuration
        from config.settings import Settings
        print("✅ Settings imported")
        
        # Test utilities
        from utils.logger import setup_logging, get_logger
        print("✅ Logger imported")
        
        # Test models (basic)
        from core.models.match_category import MatchCategoryType
        print("✅ Models imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main startup check."""
    
    print("🚀 Translation Cost Calculator - Startup Check\n")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check and fix imports
    if not check_and_fix_imports():
        return False
    
    # Create directories
    create_required_directories()
    
    # Test basic imports
    if not test_basic_imports():
        return False
    
    print("\n✅ Startup check completed successfully!")
    print("💡 Run: python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
        sys.exit(1)