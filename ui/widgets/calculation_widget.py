"""
Translation Cost Calculator - Calculation Display Widget

Widget for displaying cost calculations with detailed breakdowns and summaries.
"""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette

from utils.logger import get_logger
from utils.currency_utils import format_currency, format_rate


class SummaryPanel(QWidget):
    """Panel showing calculation summary information."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the summary panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Calculation Summary")
        title_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Summary grid
        self.summary_frame = QFrame()
        self.summary_frame.setFrameStyle(QFrame.Box)
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        
        summary_layout = QGridLayout(self.summary_frame)
        summary_layout.setContentsMargins(12, 8, 12, 8)
        summary_layout.setSpacing(6)
        
        # Create summary labels
        self.total_cost_label = QLabel("€0.00")
        self.total_cost_label.setFont(QFont("", 16, QFont.Bold))
        self.total_cost_label.setStyleSheet("color: #28a745;")
        
        self.total_words_label = QLabel("0 words")
        self.total_words_label.setFont(QFont("", 10))
        
        self.total_segments_label = QLabel("0 segments")
        self.total_segments_label.setFont(QFont("", 10))
        
        self.file_count_label = QLabel("0 files")
        self.file_count_label.setFont(QFont("", 10))
        
        self.avg_rate_label = QLabel("€0.0000/word")
        self.avg_rate_label.setFont(QFont("", 10))
        self.avg_rate_label.setStyleSheet("color: #6c757d;")
        
        # Layout summary items
        summary_layout.addWidget(QLabel("Total Cost:"), 0, 0)
        summary_layout.addWidget(self.total_cost_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Words:"), 1, 0)
        summary_layout.addWidget(self.total_words_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Segments:"), 2, 0)
        summary_layout.addWidget(self.total_segments_label, 2, 1)
        
        summary_layout.addWidget(QLabel("Files:"), 1, 2)
        summary_layout.addWidget(self.file_count_label, 1, 3)
        
        summary_layout.addWidget(QLabel("Avg. Rate:"), 2, 2)
        summary_layout.addWidget(self.avg_rate_label, 2, 3)
        
        layout.addWidget(self.summary_frame)
        
        # Project info
        self.project_frame = QFrame()
        self.project_frame.setFrameStyle(QFrame.Box)
        self.project_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 6px;
            }
        """)
        
        project_layout = QGridLayout(self.project_frame)
        project_layout.setContentsMargins(12, 8, 12, 8)
        project_layout.setSpacing(4)
        
        self.translator_label = QLabel("None selected")
        self.client_label = QLabel("None")
        self.mt_percentage_label = QLabel("70%")
        
        project_layout.addWidget(QLabel("Translator:"), 0, 0)
        project_layout.addWidget(self.translator_label, 0, 1)
        
        project_layout.addWidget(QLabel("Client:"), 1, 0)
        project_layout.addWidget(self.client_label, 1, 1)
        
        project_layout.addWidget(QLabel("MT %:"), 2, 0)
        project_layout.addWidget(self.mt_percentage_label, 2, 1)
        
        layout.addWidget(self.project_frame)
        
        layout.addStretch()
    
    def update_summary(self, calculation_info: Dict[str, Any]) -> None:
        """Update summary with calculation information.
        
        Args:
            calculation_info: Calculation information dictionary
        """
        # Update cost information
        total_cost = calculation_info.get('estimated_cost', 0.0)
        self.total_cost_label.setText(format_currency(total_cost))
        
        # Update statistics
        total_words = calculation_info.get('total_words', 0)
        total_segments = calculation_info.get('total_segments', 0)
        file_count = calculation_info.get('file_count', 0)
        
        self.total_words_label.setText(f"{total_words:,} words")
        self.total_segments_label.setText(f"{total_segments:,} segments")
        self.file_count_label.setText(f"{file_count} files")
        
        # Calculate and display average rate
        if total_words > 0 and total_cost > 0:
            avg_rate = total_cost / total_words
            self.avg_rate_label.setText(format_rate(avg_rate))
        else:
            self.avg_rate_label.setText("€0.0000/word")
        
        # Update project information
        translator = calculation_info.get('translator', 'None selected')
        client = calculation_info.get('client', 'None')
        mt_percentage = calculation_info.get('mt_percentage', 70)
        
        self.translator_label.setText(translator)
        self.client_label.setText(client)
        self.mt_percentage_label.setText(f"{mt_percentage}%")


class CategoryBreakdownTable(QTableWidget):
    """Table showing cost breakdown by match category."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the table UI."""
        # Set up columns
        headers = ["Category", "Words", "Rate", "Cost", "%"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure headers
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Category
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Words
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Rate
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Cost
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # %
        
        self.verticalHeader().setVisible(False)
        
        # Set minimum height
        self.setMinimumHeight(200)
    
    def update_breakdown(self, breakdown_data: Dict[str, Any]) -> None:
        """Update table with breakdown data.
        
        Args:
            breakdown_data: Category breakdown data
        """
        # Clear existing data
        self.setRowCount(0)
        
        # For now, show placeholder data structure
        # Full integration with real calculation service will be completed
        # when rate management and calculation are fully integrated
        
        categories = [
            ("Context Match", 125, 0.03, 3.75, 5.2),
            ("Repetitions", 89, 0.03, 2.67, 3.7),
            ("100%", 234, 0.05, 11.70, 9.7),
            ("95% - 99%", 456, 0.08, 36.48, 19.0),
            ("85% - 94%", 123, 0.10, 12.30, 5.1),
            ("75% - 84%", 78, 0.11, 8.58, 3.2),
            ("50% - 74%", 345, 0.12, 41.40, 14.3),
            ("No Match", 967, 0.12, 116.04, 40.0),
        ]
        
        total_words = sum(cat[1] for cat in categories)
        estimated_total = sum(cat[3] for cat in categories)
        
        # Add category rows
        for i, (category, words, rate, cost, percent) in enumerate(categories):
            self.insertRow(i)
            
            # Category name
            category_item = QTableWidgetItem(category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(i, 0, category_item)
            
            # Words
            words_item = QTableWidgetItem(f"{words:,}")
            words_item.setFlags(words_item.flags() & ~Qt.ItemIsEditable)
            words_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(i, 1, words_item)
            
            # Rate
            rate_item = QTableWidgetItem(format_rate(rate))
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemIsEditable)
            rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(i, 2, rate_item)
            
            # Cost
            cost_item = QTableWidgetItem(format_currency(cost))
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(i, 3, cost_item)
            
            # Percentage
            percent_item = QTableWidgetItem(f"{percent:.1f}%")
            percent_item.setFlags(percent_item.flags() & ~Qt.ItemIsEditable)
            percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(i, 4, percent_item)
        
        # Add total row
        total_row = self.rowCount()
        self.insertRow(total_row)
        
        # Style total row
        total_font = QFont()
        total_font.setBold(True)
        
        total_category_item = QTableWidgetItem("TOTAL")
        total_category_item.setFont(total_font)
        total_category_item.setFlags(total_category_item.flags() & ~Qt.ItemIsEditable)
        self.setItem(total_row, 0, total_category_item)
        
        total_words_item = QTableWidgetItem(f"{total_words:,}")
        total_words_item.setFont(total_font)
        total_words_item.setFlags(total_words_item.flags() & ~Qt.ItemIsEditable)
        total_words_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(total_row, 1, total_words_item)
        
        total_rate_item = QTableWidgetItem("—")
        total_rate_item.setFlags(total_rate_item.flags() & ~Qt.ItemIsEditable)
        total_rate_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(total_row, 2, total_rate_item)
        
        total_cost_item = QTableWidgetItem(format_currency(estimated_total))
        total_cost_item.setFont(total_font)
        total_cost_item.setFlags(total_cost_item.flags() & ~Qt.ItemIsEditable)
        total_cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_cost_item.setBackground(QPalette().highlight())
        self.setItem(total_row, 3, total_cost_item)
        
        total_percent_item = QTableWidgetItem("100.0%")
        total_percent_item.setFont(total_font)
        total_percent_item.setFlags(total_percent_item.flags() & ~Qt.ItemIsEditable)
        total_percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(total_row, 4, total_percent_item)


class CalculationWidget(QWidget):
    """Main calculation display widget with tabs and detailed breakdown."""
    
    # Signals
    recalculate_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.current_calculation_info: Optional[Dict[str, Any]] = None
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the calculation widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Summary tab
        self.summary_panel = SummaryPanel()
        self.tab_widget.addTab(self.summary_panel, "Summary")
        
        # Breakdown tab
        breakdown_widget = QWidget()
        breakdown_layout = QVBoxLayout(breakdown_widget)
        
        # Breakdown controls
        controls_layout = QHBoxLayout()
        
        breakdown_label = QLabel("Category Breakdown")
        breakdown_label.setFont(QFont("", 11, QFont.Bold))
        controls_layout.addWidget(breakdown_label)
        
        controls_layout.addStretch()
        
        self.recalculate_btn = QPushButton("Recalculate")
        self.recalculate_btn.clicked.connect(self.recalculate_requested.emit)
        controls_layout.addWidget(self.recalculate_btn)
        
        breakdown_layout.addLayout(controls_layout)
        
        # Category breakdown table
        self.breakdown_table = CategoryBreakdownTable()
        breakdown_layout.addWidget(self.breakdown_table)
        
        self.tab_widget.addTab(breakdown_widget, "Breakdown")
        
        # Details tab (placeholder for future MT/TM breakdown)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        details_info = QLabel("""
        <h3>Detailed Analysis</h3>
        <p>This tab will show:</p>
        <ul>
        <li>MT/TM breakdown for 100% matches</li>
        <li>File-by-file analysis</li>
        <li>Rate hierarchy information</li>
        <li>Minimum fee calculations</li>
        </ul>
        <p><i>Full implementation in Phase 2</i></p>
        """)
        details_info.setWordWrap(True)
        details_info.setStyleSheet("color: #666; padding: 20px;")
        details_layout.addWidget(details_info)
        details_layout.addStretch()
        
        self.tab_widget.addTab(details_widget, "Details")
        
        layout.addWidget(self.tab_widget)
        
        # Empty state
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_icon = QLabel("📊")
        empty_icon.setFont(QFont("", 48))
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_text = QLabel("No calculation available")
        empty_text.setFont(QFont("", 14, QFont.Bold))
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("color: #666;")
        empty_layout.addWidget(empty_text)
        
        empty_subtext = QLabel("Add files and select a translator to see cost calculation")
        empty_subtext.setAlignment(Qt.AlignCenter)
        empty_subtext.setStyleSheet("color: #999; font-style: italic;")
        empty_layout.addWidget(empty_subtext)
        
        layout.addWidget(self.empty_state)
        
        # Initially show empty state
        self.show_empty_state()
    
    def show_calculation_info(self, calculation_info: Dict[str, Any]) -> None:
        """Show basic calculation information.
        
        Args:
            calculation_info: Calculation information dictionary
        """
        self.current_calculation_info = calculation_info
        
        # Hide empty state, show calculation
        self.empty_state.setVisible(False)
        self.tab_widget.setVisible(True)
        
        # Estimate cost based on default rates for demo
        total_words = calculation_info.get('total_words', 0)
        estimated_cost = total_words * 0.10  # Rough estimate at 0.10 EUR/word
        calculation_info['estimated_cost'] = estimated_cost
        
        # Update summary panel
        self.summary_panel.update_summary(calculation_info)
        
        # Update breakdown table
        self.breakdown_table.update_breakdown(calculation_info)
        
        self.logger.debug(f"Updated calculation display: {total_words} words, €{estimated_cost:.2f}")
    
    def show_detailed_calculation(self, breakdown_data: Dict[str, Any]) -> None:
        """Show detailed calculation with full breakdown.
        
        Args:
            breakdown_data: Detailed breakdown data from calculation service
        """
        # This will be implemented when calculation service integration is complete
        # For now, falls back to basic info display
        self.show_calculation_info({
            'total_words': breakdown_data.get('total_words', 0),
            'total_segments': breakdown_data.get('total_segments', 0),
            'file_count': len(breakdown_data.get('files', [])),
            'estimated_cost': breakdown_data.get('total_cost', 0),
            'translator': 'From Breakdown',
            'client': 'From Breakdown',
            'mt_percentage': breakdown_data.get('mt_percentage', 70)
        })
    
    def clear_calculation(self) -> None:
        """Clear calculation display and show empty state."""
        self.current_calculation_info = None
        self.show_empty_state()
    
    def show_empty_state(self) -> None:
        """Show empty state (no calculation)."""
        self.tab_widget.setVisible(False)
        self.empty_state.setVisible(True)
    
    def show_error(self, error_message: str) -> None:
        """Show error state.
        
        Args:
            error_message: Error message to display
        """
        self.clear_calculation()
        
        # Update empty state to show error
        empty_layout = self.empty_state.layout()
        
        # Clear existing widgets
        for i in reversed(range(empty_layout.count())):
            child = empty_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add error display
        error_icon = QLabel("⚠️")
        error_icon.setFont(QFont("", 48))
        error_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(error_icon)
        
        error_title = QLabel("Calculation Error")
        error_title.setFont(QFont("", 14, QFont.Bold))
        error_title.setAlignment(Qt.AlignCenter)
        error_title.setStyleSheet("color: #dc3545;")
        empty_layout.addWidget(error_title)
        
        error_text = QLabel(error_message)
        error_text.setAlignment(Qt.AlignCenter)
        error_text.setWordWrap(True)
        error_text.setStyleSheet("color: #666; font-style: italic; max-width: 300px;")
        empty_layout.addWidget(error_text)
        
        retry_btn = QPushButton("Retry Calculation")
        retry_btn.clicked.connect(self.recalculate_requested.emit)
        empty_layout.addWidget(retry_btn)
        
        self.show_empty_state()
    
    def get_current_calculation(self) -> Optional[Dict[str, Any]]:
        """Get current calculation information.
        
        Returns:
            Optional[Dict[str, Any]]: Current calculation info or None
        """
        return self.current_calculation_info
    
    def export_calculation(self) -> Dict[str, Any]:
        """Export calculation data for external use.
        
        Returns:
            Dict[str, Any]: Exportable calculation data
        """
        if not self.current_calculation_info:
            return {}
        
        # Prepare export data
        export_data = self.current_calculation_info.copy()
        
        # Add timestamp
        from datetime import datetime
        export_data['exported_at'] = datetime.now().isoformat()
        
        # Add breakdown table data
        breakdown_data = []
        table = self.breakdown_table
        
        for row in range(table.rowCount() - 1):  # Exclude total row
            category = table.item(row, 0).text()
            words = table.item(row, 1).text()
            rate = table.item(row, 2).text()
            cost = table.item(row, 3).text()
            percent = table.item(row, 4).text()
            
            breakdown_data.append({
                'category': category,
                'words': words,
                'rate': rate,
                'cost': cost,
                'percent': percent
            })
        
        export_data['breakdown'] = breakdown_data
        
        return export_data
    
    def update_mt_percentage(self, mt_percentage: int) -> None:
        """Update MT percentage in current calculation.
        
        Args:
            mt_percentage: New MT percentage
        """
        if self.current_calculation_info:
            self.current_calculation_info['mt_percentage'] = mt_percentage
            self.summary_panel.update_summary(self.current_calculation_info)
    
    def get_selected_category(self) -> Optional[str]:
        """Get currently selected category in breakdown table.
        
        Returns:
            Optional[str]: Selected category name or None
        """
        current_row = self.breakdown_table.currentRow()
        if current_row >= 0 and current_row < self.breakdown_table.rowCount() - 1:  # Exclude total row
            return self.breakdown_table.item(current_row, 0).text()
        return None