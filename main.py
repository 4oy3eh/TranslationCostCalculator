#!/usr/bin/env python3
"""
Translation Cost Calculator - Main Application Entry Point

Desktop application for calculating translation costs from CAT analysis files.
Supports Trados CSV, Phrase JSON, and Excel formats with professional PDF export.

Author: Translation Cost Calculator Team
License: Proprietary
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from config.database import DatabaseManager
from utils.logger import setup_logging
from ui.main_window import MainWindow


class TranslationCostCalculator:
    """Main application class coordinating all components."""
    
    def __init__(self):
        self.app: QApplication = None
        self.main_window: MainWindow = None
        self.db_manager: DatabaseManager = None
        
    def initialize_application(self) -> bool:
        """Initialize all application components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Setup logging
            setup_logging()
            logging.info("Starting Translation Cost Calculator")
            
            # Initialize database
            self.db_manager = DatabaseManager()
            if not self.db_manager.initialize():
                logging.error("Failed to initialize database")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Application initialization failed: {e}")
            return False
    
    def create_gui(self) -> bool:
        """Create and show the main GUI window.
        
        Returns:
            bool: True if GUI creation successful, False otherwise
        """
        try:
            self.main_window = MainWindow()
            self.main_window.show()
            return True
            
        except Exception as e:
            logging.error(f"GUI creation failed: {e}")
            self.show_error_dialog("GUI Error", f"Failed to create user interface: {e}")
            return False
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """Show error dialog to user.
        
        Args:
            title: Dialog title
            message: Error message to display
        """
        if self.app:
            QMessageBox.critical(None, title, message)
        else:
            print(f"ERROR: {title} - {message}")
    
    def run(self) -> int:
        """Run the main application loop.
        
        Returns:
            int: Application exit code
        """
        try:
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(Settings.APP_NAME)
            self.app.setApplicationVersion(Settings.APP_VERSION)
            self.app.setOrganizationName(Settings.ORGANIZATION)
            
            # Set application icon if available
            icon_path = project_root / "assets" / "icon.ico"
            if icon_path.exists():
                self.app.setWindowIcon(QIcon(str(icon_path)))
            
            # Initialize application components
            if not self.initialize_application():
                self.show_error_dialog("Initialization Error", 
                                     "Failed to initialize application components")
                return 1
            
            # Create and show GUI
            if not self.create_gui():
                return 1
            
            # Run application event loop
            return self.app.exec()
            
        except Exception as e:
            logging.error(f"Application execution failed: {e}")
            self.show_error_dialog("Application Error", f"Unexpected error: {e}")
            return 1
        
        finally:
            # Cleanup
            if self.db_manager:
                self.db_manager.close()
            logging.info("Translation Cost Calculator shutdown complete")


def main() -> int:
    """Application entry point.
    
    Returns:
        int: Application exit code
    """
    calculator = TranslationCostCalculator()
    return calculator.run()


if __name__ == "__main__":
    sys.exit(main())