"""
Translation Cost Calculator - Main Application Window

Main window with splitter layout, file management, and calculation display.
Integrates all UI components and coordinates with business services.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QAction, QIcon, QFont, QPixmap

from config.settings import Settings
from config.database import DatabaseManager
from core.services.calculation_service import CalculationService
from core.services.project_service import ProjectService
from core.repositories.translator_repository import TranslatorRepository, ClientRepository
from core.models.project import Project
from core.models.translator import Translator, Client
from ui.widgets.file_list_widget import FileListWidget
from ui.widgets.calculation_widget import CalculationWidget
from utils.validation import ValidationResult
from utils.logger import get_logger


class FileProcessor(QObject):
    """Background file processor to avoid UI blocking."""
    
    file_processed = Signal(dict)  # Emits processing results
    progress_updated = Signal(int)  # Emits progress percentage
    error_occurred = Signal(str)   # Emits error message
    
    def __init__(self, project_service: ProjectService):
        super().__init__()
        self.project_service = project_service
        self.logger = get_logger(__name__)
    
    def process_file(self, file_path: Path, project_id: Optional[int] = None):
        """Process uploaded file in background thread.
        
        Args:
            file_path: Path to file to process
            project_id: Optional project ID to add file to
        """
        try:
            self.progress_updated.emit(25)
            
            # Process the file
            result = self.project_service.process_uploaded_file(file_path, project_id)
            
            self.progress_updated.emit(75)
            
            # Emit results
            self.file_processed.emit(result)
            self.progress_updated.emit(100)
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window with full functionality."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize logger first
        self.logger = get_logger(__name__)
        
        # Initialize database FIRST
        self.db_manager = DatabaseManager()
        if not self.db_manager.initialize():
            QMessageBox.critical(None, "Database Error", 
                               "Failed to initialize database. Application will exit.")
            sys.exit(1)
        
        # Initialize services AFTER database is ready
        self.calculation_service = CalculationService(self.db_manager)
        self.project_service = ProjectService(self.db_manager)
        self.translator_repository = TranslatorRepository(self.db_manager)
        self.client_repository = ClientRepository(self.db_manager)
        
        # Initialize state
        self.current_project: Optional[Project] = None
        self.current_translator: Optional[Translator] = None
        self.current_client: Optional[Client] = None
        
        # UI components
        self.file_list_widget: Optional[FileListWidget] = None
        self.calculation_widget: Optional[CalculationWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # Background processing
        self.file_processor = FileProcessor(self.project_service)
        self.processing_thread = QThread()
        self.file_processor.moveToThread(self.processing_thread)
        self.processing_thread.start()
        
        # Setup UI
        self.init_ui()
        self.setup_connections()
        self.load_initial_data()
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(f"{Settings.APP_NAME} v{Settings.APP_VERSION}")
        self.setMinimumSize(*Settings.MAIN_WINDOW_MIN_SIZE)
        self.resize(*Settings.MAIN_WINDOW_DEFAULT_SIZE)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add project selection bar
        self.create_project_bar(layout)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create left panel (file list)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Create right panel (calculation display)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes(Settings.SPLITTER_PROPORTIONS)
        splitter.setStretchFactor(0, 0)  # Fixed left panel
        splitter.setStretchFactor(1, 1)  # Expandable right panel
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_styling()
    
    def create_project_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create project selection and settings bar.
        
        Args:
            parent_layout: Parent layout to add to
        """
        project_group = QGroupBox("Project Settings")
        project_layout = QFormLayout(project_group)
        
        # Project selection
        project_layout_h = QHBoxLayout()
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setEditable(False)
        project_layout_h.addWidget(self.project_combo)
        
        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.clicked.connect(self.new_project)
        project_layout_h.addWidget(self.new_project_btn)
        
        project_layout_h.addStretch()
        project_layout.addRow("Project:", project_layout_h)
        
        # Translator selection
        translator_layout_h = QHBoxLayout()
        
        self.translator_combo = QComboBox()
        self.translator_combo.setMinimumWidth(200)
        translator_layout_h.addWidget(self.translator_combo)
        
        self.manage_translators_btn = QPushButton("Manage")
        self.manage_translators_btn.clicked.connect(self.manage_translators)
        translator_layout_h.addWidget(self.manage_translators_btn)
        
        translator_layout_h.addStretch()
        project_layout.addRow("Translator:", translator_layout_h)
        
        # Client selection (optional)
        client_layout_h = QHBoxLayout()
        
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(200)
        self.client_combo.addItem("(No Client)", None)
        client_layout_h.addWidget(self.client_combo)
        
        self.manage_clients_btn = QPushButton("Manage")
        self.manage_clients_btn.clicked.connect(self.manage_clients)
        client_layout_h.addWidget(self.manage_clients_btn)
        
        client_layout_h.addStretch()
        project_layout.addRow("Client:", client_layout_h)
        
        # MT Percentage
        mt_layout_h = QHBoxLayout()
        
        self.mt_percentage_spin = QSpinBox()
        self.mt_percentage_spin.setRange(0, 100)
        self.mt_percentage_spin.setValue(Settings.DEFAULT_MT_PERCENTAGE)
        self.mt_percentage_spin.setSuffix("%")
        mt_layout_h.addWidget(self.mt_percentage_spin)
        
        mt_info_label = QLabel("(for 100% matches)")
        mt_info_label.setStyleSheet("color: #666; font-style: italic;")
        mt_layout_h.addWidget(mt_info_label)
        
        mt_layout_h.addStretch()
        project_layout.addRow("MT Percentage:", mt_layout_h)
        
        parent_layout.addWidget(project_group)
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with file list.
        
        Returns:
            QWidget: Left panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # File list header
        header_layout = QHBoxLayout()
        
        files_label = QLabel("Project Files")
        files_label.setFont(QFont("", 12, QFont.Bold))
        header_layout.addWidget(files_label)
        
        header_layout.addStretch()
        
        # Add file button
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        header_layout.addWidget(self.add_file_btn)
        
        layout.addLayout(header_layout)
        
        # File list widget
        self.file_list_widget = FileListWidget()
        self.file_list_widget.file_selected.connect(self.on_file_selected)
        self.file_list_widget.file_removed.connect(self.on_file_removed)
        layout.addWidget(self.file_list_widget)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with calculation display.
        
        Returns:
            QWidget: Right panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Calculation header
        header_layout = QHBoxLayout()
        
        calc_label = QLabel("Cost Calculation")
        calc_label.setFont(QFont("", 12, QFont.Bold))
        header_layout.addWidget(calc_label)
        
        header_layout.addStretch()
        
        # Export button (stub)
        self.export_btn = QPushButton("Export PDF")
        self.export_btn.clicked.connect(self.export_pdf)
        self.export_btn.setEnabled(False)  # Disabled until Phase 2
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Calculation widget
        self.calculation_widget = CalculationWidget()
        layout.addWidget(self.calculation_widget)
        
        return panel
    
    def create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("&Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        add_file_action = QAction("&Add File", self)
        add_file_action.setShortcut("Ctrl+A")
        add_file_action.triggered.connect(self.add_file)
        file_menu.addAction(add_file_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        manage_translators_action = QAction("Manage &Translators", self)
        manage_translators_action.triggered.connect(self.manage_translators)
        edit_menu.addAction(manage_translators_action)
        
        manage_clients_action = QAction("Manage &Clients", self)
        manage_clients_action.triggered.connect(self.manage_clients)
        edit_menu.addAction(manage_clients_action)
        
        manage_rates_action = QAction("Manage &Rates", self)
        manage_rates_action.triggered.connect(self.manage_rates)
        edit_menu.addAction(manage_rates_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self) -> None:
        """Create application toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # New project
        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # Add file
        add_file_action = QAction("Add File", self)
        add_file_action.triggered.connect(self.add_file)
        toolbar.addAction(add_file_action)
        
        toolbar.addSeparator()
        
        # Calculate
        self.calculate_action = QAction("Calculate", self)
        self.calculate_action.triggered.connect(self.calculate_costs)
        self.calculate_action.setEnabled(False)
        toolbar.addAction(self.calculate_action)
    
    def create_status_bar(self) -> None:
        """Create status bar with progress indicator."""
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Version label
        version_label = QLabel(f"v{Settings.APP_VERSION}")
        version_label.setStyleSheet("color: #666;")
        self.status_bar.addPermanentWidget(version_label)
    
    def apply_styling(self) -> None:
        """Apply custom styling to the window."""
        # Load QSS file if it exists
        style_file = Path(__file__).parent / "styles" / "main_style.qss"
        
        if style_file.exists():
            try:
                with open(style_file, 'r') as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                self.logger.warning(f"Could not load stylesheet: {e}")
        
        # Set window icon if available
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def setup_connections(self) -> None:
        """Setup signal connections."""
        # Combo box connections
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        self.translator_combo.currentTextChanged.connect(self.on_translator_changed)
        self.client_combo.currentTextChanged.connect(self.on_client_changed)
        self.mt_percentage_spin.valueChanged.connect(self.on_mt_percentage_changed)
        
        # File processor connections
        self.file_processor.file_processed.connect(self.on_file_processed)
        self.file_processor.progress_updated.connect(self.on_progress_updated)
        self.file_processor.error_occurred.connect(self.on_processing_error)
    
    def load_initial_data(self) -> None:
        """Load initial data into UI components."""
        try:
            # Load translators
            translators = self.translator_repository.find_active_translators()
            self.translator_combo.clear()
            self.translator_combo.addItem("Select Translator...", None)
            for translator in translators:
                self.translator_combo.addItem(translator.get_display_name(), translator.id)
            
            # Load clients
            clients = self.client_repository.find_active_clients()
            self.client_combo.clear()
            self.client_combo.addItem("(No Client)", None)
            for client in clients:
                self.client_combo.addItem(client.get_display_name(), client.id)
            
            # Load projects (initially empty)
            self.project_combo.clear()
            self.project_combo.addItem("No Project Selected", None)
            
            self.status_label.setText("Data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self.show_error("Error", f"Failed to load initial data: {e}")
    
    def refresh_data(self) -> None:
        """Refresh all data in the UI."""
        self.load_initial_data()
        if self.current_project:
            self.load_project_files()
        self.status_label.setText("Data refreshed")
    
    # Project Management
    def new_project(self) -> None:
        """Create a new project (stub)."""
        # STUB: Will be implemented with full dialog in Phase 2
        QMessageBox.information(
            self, "New Project", 
            "New project dialog will be implemented in Phase 2.\n\n"
            "For now, use the project settings above to configure calculation parameters."
        )
    
    def open_project(self) -> None:
        """Open an existing project (stub)."""
        # STUB: Will be implemented with project browser in Phase 2
        QMessageBox.information(
            self, "Open Project",
            "Project browser will be implemented in Phase 2.\n\n"
            "For now, files can be added directly for calculation."
        )
    
    def on_project_changed(self, project_name: str) -> None:
        """Handle project selection change.
        
        Args:
            project_name: Selected project name
        """
        project_id = self.project_combo.currentData()
        if project_id:
            self.current_project = self.project_service.load_project(project_id)
            if self.current_project:
                self.load_project_files()
                self.update_calculation()
                self.status_label.setText(f"Loaded project: {project_name}")
        else:
            self.current_project = None
            self.file_list_widget.clear_files()
            self.calculation_widget.clear_calculation()
    
    def load_project_files(self) -> None:
        """Load files for the current project."""
        if not self.current_project:
            return
        
        try:
            files = self.project_service.get_project_files(self.current_project.id)
            self.file_list_widget.set_files(files)
        except Exception as e:
            self.logger.error(f"Error loading project files: {e}")
            self.show_error("Error", f"Failed to load project files: {e}")
    
    # Translator and Client Management
    def on_translator_changed(self, translator_name: str) -> None:
        """Handle translator selection change.
        
        Args:
            translator_name: Selected translator name
        """
        translator_id = self.translator_combo.currentData()
        if translator_id:
            self.current_translator = self.translator_repository.find_by_id(translator_id)
            self.update_calculation()
            self.status_label.setText(f"Selected translator: {translator_name}")
    
    def on_client_changed(self, client_name: str) -> None:
        """Handle client selection change.
        
        Args:
            client_name: Selected client name
        """
        client_id = self.client_combo.currentData()
        if client_id:
            self.current_client = self.client_repository.find_by_id(client_id)
        else:
            self.current_client = None
        
        self.update_calculation()
        if client_name != "(No Client)":
            self.status_label.setText(f"Selected client: {client_name}")
    
    def on_mt_percentage_changed(self, value: int) -> None:
        """Handle MT percentage change.
        
        Args:
            value: New MT percentage value
        """
        self.update_calculation()
        self.status_label.setText(f"MT percentage changed to {value}%")
    
    def manage_translators(self) -> None:
        """Open translator management dialog (stub)."""
        # STUB: Will be implemented in Phase 2
        QMessageBox.information(
            self, "Manage Translators",
            "Translator management dialog will be implemented in Phase 2."
        )
    
    def manage_clients(self) -> None:
        """Open client management dialog (stub)."""
        # STUB: Will be implemented in Phase 2
        QMessageBox.information(
            self, "Manage Clients",
            "Client management dialog will be implemented in Phase 2."
        )
    
    def manage_rates(self) -> None:
        """Open rate management dialog (stub)."""
        # STUB: Will be implemented in Phase 2
        QMessageBox.information(
            self, "Manage Rates",
            "Rate management dialog will be implemented in Phase 2."
        )
    
    # File Management
    def add_file(self) -> None:
        """Add a file to the current project."""
        # Get supported file types
        supported_types = self.project_service.get_supported_file_types()
        extensions = supported_types.get('extensions', ['.csv'])
        
        # Create filter string
        filter_parts = []
        for ext in extensions:
            filter_parts.append(f"*{ext}")
        
        file_filter = f"Supported Files ({' '.join(filter_parts)});;All Files (*.*)"
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Analysis File",
            "",
            file_filter
        )
        
        if file_path:
            self.process_file(Path(file_path))
    
    def process_file(self, file_path: Path) -> None:
        """Process a file in background thread.
        
        Args:
            file_path: Path to file to process
        """
        self.show_progress("Processing file...")
        self.file_processor.process_file(file_path, 
                                       self.current_project.id if self.current_project else None)
    
    def on_file_processed(self, result: Dict[str, Any]) -> None:
        """Handle file processing completion.
        
        Args:
            result: Processing result dictionary
        """
        self.hide_progress()
        
        if result.get('success'):
            # Update file list
            if self.current_project:
                self.load_project_files()
            else:
                # Add file to temporary list for calculation
                file_info = result.get('file_info', {})
                analysis_data = result.get('analysis_data', {})
                
                self.file_list_widget.add_temporary_file({
                    'filename': file_info.get('name', 'Unknown'),
                    'total_words': analysis_data.get('total_words', 0),
                    'total_segments': analysis_data.get('total_segments', 0),
                    'language_pair': f"{analysis_data.get('source_language', '')}>{analysis_data.get('target_language', '')}",
                    'cat_tool': analysis_data.get('cat_tool', 'Unknown')
                })
            
            # Update calculation
            self.update_calculation()
            
            # Show success message
            filename = result.get('file_info', {}).get('name', 'file')
            self.status_label.setText(f"Successfully processed: {filename}")
            
            # Show warnings if any
            warnings = result.get('warnings', [])
            if warnings:
                warning_text = "\n".join(warnings)
                QMessageBox.warning(self, "Processing Warnings", warning_text)
        else:
            # Show errors
            errors = result.get('errors', ['Unknown error'])
            error_text = "\n".join(errors)
            self.show_error("File Processing Error", error_text)
    
    def on_file_selected(self, file_data: Dict[str, Any]) -> None:
        """Handle file selection in the file list.
        
        Args:
            file_data: Selected file data
        """
        # Update status
        filename = file_data.get('filename', 'Unknown')
        words = file_data.get('total_words', 0)
        self.status_label.setText(f"Selected: {filename} ({words:,} words)")
    
    def on_file_removed(self, file_data: Dict[str, Any]) -> None:
        """Handle file removal from the file list.
        
        Args:
            file_data: Removed file data
        """
        if self.current_project and 'id' in file_data:
            # Remove from project
            success = self.project_service.remove_file_from_project(
                self.current_project.id, file_data['id']
            )
            
            if success:
                self.load_project_files()
                self.update_calculation()
                self.status_label.setText(f"Removed file: {file_data.get('filename', 'Unknown')}")
            else:
                self.show_error("Error", "Failed to remove file from project")
        else:
            # Remove from temporary list
            self.update_calculation()
            self.status_label.setText(f"Removed file: {file_data.get('filename', 'Unknown')}")
    
    # Calculation
    def calculate_costs(self) -> None:
        """Calculate costs for current files."""
        self.update_calculation()
        self.status_label.setText("Calculation updated")
    
    def update_calculation(self) -> None:
        """Update cost calculation display."""
        if not self.current_translator:
            self.calculation_widget.clear_calculation()
            self.calculate_action.setEnabled(False)
            return
        
        try:
            # Get files to calculate
            files = self.file_list_widget.get_files()
            if not files:
                self.calculation_widget.clear_calculation()
                self.calculate_action.setEnabled(False)
                return
            
            # Enable calculate action
            self.calculate_action.setEnabled(True)
            
            # For now, show basic calculation info
            # Full calculation integration will be completed when 
            # calculation service is properly integrated with parsed file data
            
            total_words = sum(f.get('total_words', 0) for f in files)
            total_segments = sum(f.get('total_segments', 0) for f in files)
            
            calculation_info = {
                'total_words': total_words,
                'total_segments': total_segments,
                'file_count': len(files),
                'translator': self.current_translator.name if self.current_translator else 'None',
                'client': self.current_client.name if self.current_client else 'None',
                'mt_percentage': self.mt_percentage_spin.value()
            }
            
            self.calculation_widget.show_calculation_info(calculation_info)
            
        except Exception as e:
            self.logger.error(f"Error updating calculation: {e}")
            self.calculation_widget.show_error(f"Calculation error: {e}")
    
    # Export
    def export_pdf(self) -> None:
        """Export calculation as PDF (stub)."""
        # STUB: Will be implemented in Phase 2
        QMessageBox.information(
            self, "Export PDF",
            "PDF export will be implemented in Phase 2."
        )
    
    # Progress and Status
    def show_progress(self, message: str) -> None:
        """Show progress bar with message.
        
        Args:
            message: Status message to display
        """
        self.status_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def hide_progress(self) -> None:
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
    
    def on_progress_updated(self, value: int) -> None:
        """Handle progress update.
        
        Args:
            value: Progress percentage
        """
        self.progress_bar.setValue(value)
    
    def on_processing_error(self, error_message: str) -> None:
        """Handle processing error.
        
        Args:
            error_message: Error message
        """
        self.hide_progress()
        self.show_error("Processing Error", error_message)
    
    # Utility Methods
    def show_error(self, title: str, message: str) -> None:
        """Show error message dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self, title, message)
        self.status_label.setText("Error occurred")
    
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self, 
            f"About {Settings.APP_NAME}",
            f"""
            <h3>{Settings.APP_NAME}</h3>
            <p>Version {Settings.APP_VERSION}</p>
            <p>Professional translation cost calculation from CAT analysis files.</p>
            <p>Supports Trados CSV, Phrase JSON, and Excel formats.</p>
            <p><b>Phase 1 - Basic Functionality</b></p>
            <p>© 2025 Translation Cost Calculator Team</p>
            """
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Clean up background thread
        self.processing_thread.quit()
        self.processing_thread.wait()
        
        # Close database connection
        if self.db_manager:
            self.db_manager.close()
        
        event.accept()