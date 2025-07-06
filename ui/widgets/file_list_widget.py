"""
Translation Cost Calculator - File List Widget

Custom widget for managing project files with display, selection, and removal.
"""

import logging
import sys
from typing import List, Dict, Any, Optional

# Ensure PySide6 is available
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QPushButton, QLabel, QFrame, QMenu, QMessageBox
    )
    from PySide6.QtCore import Qt, Signal, QSize
    from PySide6.QtGui import QFont, QIcon, QAction
except ImportError as e:
    print(f"❌ PySide6 import failed: {e}")
    print("💡 Install with: pip install PySide6")
    sys.exit(1)

from utils.logger import get_logger


class FileItemWidget(QWidget):
    """Custom widget for displaying file information in the list."""
    
    def __init__(self, file_data: Dict[str, Any]):
        super().__init__()
        self.file_data = file_data
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the file item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Main info layout
        main_layout = QHBoxLayout()
        
        # File icon/type indicator
        type_label = QLabel()
        cat_tool = self.file_data.get('cat_tool', 'Unknown')
        
        if cat_tool == 'Trados':
            type_label.setText("📊")  # Chart emoji for Trados
        elif cat_tool == 'Phrase':
            type_label.setText("📋")  # Clipboard emoji for Phrase
        elif cat_tool == 'Excel':
            type_label.setText("📈")  # Excel-like emoji
        else:
            type_label.setText("📄")  # Document emoji for unknown
        
        type_label.setFont(QFont("", 16))
        type_label.setFixedSize(24, 24)
        main_layout.addWidget(type_label)
        
        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        
        # Filename
        filename = self.file_data.get('filename', 'Unknown File')
        filename_label = QLabel(filename)
        filename_label.setFont(QFont("", 9, QFont.Bold))
        filename_label.setWordWrap(True)
        info_layout.addWidget(filename_label)
        
        # Statistics
        words = self.file_data.get('total_words', 0)
        segments = self.file_data.get('total_segments', 0)
        language_pair = self.file_data.get('language_pair', '')
        
        stats_text = f"{words:,} words, {segments:,} segments"
        if language_pair:
            stats_text += f" | {language_pair}"
        
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont("", 8))
        stats_label.setStyleSheet("color: #666;")
        info_layout.addWidget(stats_label)
        
        main_layout.addLayout(info_layout, 1)
        
        # Status indicator
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        # CAT tool label
        tool_label = QLabel(cat_tool)
        tool_label.setFont(QFont("", 7))
        tool_label.setStyleSheet("""
            background-color: #e3f2fd;
            color: #1976d2;
            border-radius: 8px;
            padding: 2px 6px;
        """)
        tool_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(tool_label)
        
        # Temporary file indicator
        if self.file_data.get('is_temporary', False):
            temp_label = QLabel("TEMP")
            temp_label.setFont(QFont("", 7))
            temp_label.setStyleSheet("""
                background-color: #fff3e0;
                color: #f57c00;
                border-radius: 8px;
                padding: 2px 6px;
            """)
            temp_label.setAlignment(Qt.AlignCenter)
            status_layout.addWidget(temp_label)
        
        main_layout.addLayout(status_layout)
        
        layout.addLayout(main_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(separator)
    
    def get_file_data(self) -> Dict[str, Any]:
        """Get the file data for this item.
        
        Returns:
            Dict[str, Any]: File data
        """
        return self.file_data


class FileListWidget(QWidget):
    """Widget for managing a list of project files."""
    
    # Signals
    file_selected = Signal(dict)  # Emitted when a file is selected
    file_removed = Signal(dict)   # Emitted when a file is removed
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.files: List[Dict[str, Any]] = []
        self.temporary_files: List[Dict[str, Any]] = []
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.itemClicked.connect(self.on_item_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set minimum size for file list
        self.file_list.setMinimumHeight(200)
        
        layout.addWidget(self.file_list)
        
        # Empty state label
        self.empty_label = QLabel("No files added yet.\nUse 'Add File' to start.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #999;
            font-style: italic;
            padding: 20px;
        """)
        self.empty_label.setVisible(True)
        layout.addWidget(self.empty_label)
        
        # File summary
        self.summary_frame = QFrame()
        self.summary_frame.setFrameStyle(QFrame.Box)
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(8, 4, 8, 4)
        
        self.summary_label = QLabel("0 files, 0 words")
        self.summary_label.setFont(QFont("", 8, QFont.Bold))
        summary_layout.addWidget(self.summary_label)
        
        summary_layout.addStretch()
        
        # Clear all button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setFont(QFont("", 8))
        self.clear_btn.clicked.connect(self.clear_all_files)
        self.clear_btn.setVisible(False)
        summary_layout.addWidget(self.clear_btn)
        
        layout.addWidget(self.summary_frame)
        self.summary_frame.setVisible(False)
    
    def set_files(self, files: List[Dict[str, Any]]) -> None:
        """Set the list of files to display.
        
        Args:
            files: List of file data dictionaries
        """
        self.files = files.copy()
        self.refresh_display()
    
    def add_temporary_file(self, file_data: Dict[str, Any]) -> None:
        """Add a temporary file (not saved to project).
        
        Args:
            file_data: File data dictionary
        """
        file_data['is_temporary'] = True
        self.temporary_files.append(file_data)
        self.refresh_display()
    
    def get_files(self) -> List[Dict[str, Any]]:
        """Get all files (permanent + temporary).
        
        Returns:
            List[Dict[str, Any]]: All file data
        """
        return self.files + self.temporary_files
    
    def clear_files(self) -> None:
        """Clear all files from the list."""
        self.files.clear()
        self.temporary_files.clear()
        self.refresh_display()
    
    def clear_temporary_files(self) -> None:
        """Clear only temporary files."""
        self.temporary_files.clear()
        self.refresh_display()
    
    def clear_all_files(self) -> None:
        """Clear all files with confirmation."""
        if not self.get_files():
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All Files",
            "Are you sure you want to remove all files?\n\n"
            "This will clear temporary files. Project files will remain in the project.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_temporary_files()
    
    def refresh_display(self) -> None:
        """Refresh the file list display."""
        # Clear current items
        self.file_list.clear()
        
        all_files = self.get_files()
        
        if not all_files:
            # Show empty state
            self.empty_label.setVisible(True)
            self.summary_frame.setVisible(False)
            self.file_list.setVisible(False)
            return
        
        # Hide empty state
        self.empty_label.setVisible(False)
        self.summary_frame.setVisible(True)
        self.file_list.setVisible(True)
        
        # Add files to list
        for file_data in all_files:
            self.add_file_item(file_data)
        
        # Update summary
        self.update_summary()
    
    def add_file_item(self, file_data: Dict[str, Any]) -> None:
        """Add a file item to the list.
        
        Args:
            file_data: File data dictionary
        """
        # Create list item
        item = QListWidgetItem()
        
        # Create custom widget
        widget = FileItemWidget(file_data)
        
        # Set item size
        item.setSizeHint(widget.sizeHint())
        
        # Add to list
        self.file_list.addItem(item)
        self.file_list.setItemWidget(item, widget)
    
    def update_summary(self) -> None:
        """Update the summary display."""
        all_files = self.get_files()
        
        if not all_files:
            self.clear_btn.setVisible(False)
            return
        
        file_count = len(all_files)
        total_words = sum(f.get('total_words', 0) for f in all_files)
        total_segments = sum(f.get('total_segments', 0) for f in all_files)
        
        # Count temporary files
        temp_count = len(self.temporary_files)
        
        summary_text = f"{file_count} files, {total_words:,} words, {total_segments:,} segments"
        if temp_count > 0:
            summary_text += f" ({temp_count} temporary)"
        
        self.summary_label.setText(summary_text)
        self.clear_btn.setVisible(temp_count > 0)
    
    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click.
        
        Args:
            item: Clicked list item
        """
        widget = self.file_list.itemWidget(item)
        if isinstance(widget, FileItemWidget):
            file_data = widget.get_file_data()
            self.file_selected.emit(file_data)
    
    def show_context_menu(self, position) -> None:
        """Show context menu for file operations.
        
        Args:
            position: Mouse position
        """
        item = self.file_list.itemAt(position)
        if not item:
            return
        
        widget = self.file_list.itemWidget(item)
        if not isinstance(widget, FileItemWidget):
            return
        
        file_data = widget.get_file_data()
        
        # Create context menu
        menu = QMenu(self)
        
        # View details action
        details_action = QAction("View Details", self)
        details_action.triggered.connect(lambda: self.show_file_details(file_data))
        menu.addAction(details_action)
        
        menu.addSeparator()
        
        # Remove action
        remove_action = QAction("Remove File", self)
        remove_action.triggered.connect(lambda: self.remove_file(file_data))
        menu.addAction(remove_action)
        
        # Show menu
        menu.exec(self.file_list.mapToGlobal(position))
    
    def show_file_details(self, file_data: Dict[str, Any]) -> None:
        """Show detailed file information.
        
        Args:
            file_data: File data to show
        """
        details = []
        details.append(f"<b>Filename:</b> {file_data.get('filename', 'Unknown')}")
        details.append(f"<b>Words:</b> {file_data.get('total_words', 0):,}")
        details.append(f"<b>Segments:</b> {file_data.get('total_segments', 0):,}")
        details.append(f"<b>Language Pair:</b> {file_data.get('language_pair', 'Unknown')}")
        details.append(f"<b>CAT Tool:</b> {file_data.get('cat_tool', 'Unknown')}")
        
        if file_data.get('is_temporary'):
            details.append(f"<b>Status:</b> Temporary (not saved to project)")
        else:
            details.append(f"<b>Status:</b> Saved to project")
        
        if file_data.get('created_at'):
            details.append(f"<b>Added:</b> {file_data['created_at']}")
        
        details_text = "<br>".join(details)
        
        QMessageBox.information(
            self,
            "File Details",
            details_text
        )
    
    def remove_file(self, file_data: Dict[str, Any]) -> None:
        """Remove a file from the list.
        
        Args:
            file_data: File data to remove
        """
        # Confirm removal
        filename = file_data.get('filename', 'Unknown')
        is_temporary = file_data.get('is_temporary', False)
        
        if is_temporary:
            message = f"Remove temporary file '{filename}'?"
        else:
            message = f"Remove '{filename}' from the project?\n\nThis action cannot be undone."
        
        reply = QMessageBox.question(
            self,
            "Remove File",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Remove from appropriate list
        if is_temporary:
            try:
                self.temporary_files.remove(file_data)
                self.refresh_display()
                self.file_removed.emit(file_data)
            except ValueError:
                self.logger.warning(f"Temporary file not found in list: {filename}")
        else:
            # Remove from permanent files (will be handled by parent)
            self.file_removed.emit(file_data)
    
    def get_selected_file(self) -> Optional[Dict[str, Any]]:
        """Get currently selected file data.
        
        Returns:
            Optional[Dict[str, Any]]: Selected file data or None
        """
        current_item = self.file_list.currentItem()
        if not current_item:
            return None
        
        widget = self.file_list.itemWidget(current_item)
        if isinstance(widget, FileItemWidget):
            return widget.get_file_data()
        
        return None
    
    def select_file_by_filename(self, filename: str) -> bool:
        """Select a file by filename.
        
        Args:
            filename: Filename to select
            
        Returns:
            bool: True if file was found and selected
        """
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            
            if isinstance(widget, FileItemWidget):
                file_data = widget.get_file_data()
                if file_data.get('filename') == filename:
                    self.file_list.setCurrentItem(item)
                    self.file_selected.emit(file_data)
                    return True
        
        return False