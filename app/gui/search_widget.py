"""
Global Search & Filter Widget - Instant find across all data
SUPERCHARGED: Fuzzy search, live filtering, keyboard navigation
"""
import logging
from typing import List, Dict, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                            QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QLabel, QCheckBox, QGroupBox, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
import re

logger = logging.getLogger(__name__)


class SearchWidget(QWidget):
    """
    Global search and filter widget

    Features:
    - Instant search across all articles, sources, citations
    - Fuzzy matching (typo-tolerant)
    - Live filtering with debouncing
    - Quick filters (errors, pending, completed)
    - Search history
    - Keyboard navigation (Ctrl+F, Enter, Esc)
    - Result highlighting
    - Export results
    """

    # Signals
    result_selected = pyqtSignal(dict)  # Emitted when user selects a result
    filter_changed = pyqtSignal(dict)   # Emitted when filters change

    def __init__(self, orchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.all_data = []  # All searchable items
        self.filtered_data = []  # Currently filtered items
        self.search_history = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search bar
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search articles, sources, citations... (Ctrl+F)")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_search_return_pressed)
        search_layout.addWidget(self.search_input)

        # Search type dropdown
        self.search_type = QComboBox()
        self.search_type.addItems(['All', 'Articles', 'Sources', 'Citations', 'Errors'])
        self.search_type.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_type)

        # Search mode
        self.fuzzy_checkbox = QCheckBox("Fuzzy")
        self.fuzzy_checkbox.setChecked(True)
        self.fuzzy_checkbox.setToolTip("Allow typos and partial matches")
        self.fuzzy_checkbox.stateChanged.connect(self.apply_filters)
        search_layout.addWidget(self.fuzzy_checkbox)

        # Case sensitive
        self.case_sensitive = QCheckBox("Case")
        self.case_sensitive.setToolTip("Case sensitive search")
        self.case_sensitive.stateChanged.connect(self.apply_filters)
        search_layout.addWidget(self.case_sensitive)

        # Regex mode
        self.regex_checkbox = QCheckBox("Regex")
        self.regex_checkbox.setToolTip("Use regular expressions")
        self.regex_checkbox.stateChanged.connect(self.apply_filters)
        search_layout.addWidget(self.regex_checkbox)

        layout.addLayout(search_layout)

        # Quick filters
        filters_group = QGroupBox("Quick Filters")
        filters_layout = QHBoxLayout()

        self.filter_pending = QCheckBox("Pending")
        self.filter_pending.stateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_pending)

        self.filter_in_progress = QCheckBox("In Progress")
        self.filter_in_progress.stateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_in_progress)

        self.filter_completed = QCheckBox("Completed")
        self.filter_completed.stateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_completed)

        self.filter_errors = QCheckBox("Errors")
        self.filter_errors.stateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_errors)

        self.filter_review_required = QCheckBox("Review Required")
        self.filter_review_required.stateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_review_required)

        filters_layout.addStretch()

        # Clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_filters_btn)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Results count
        self.results_label = QLabel("0 results")
        layout.addWidget(self.results_label)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            'Type', 'ID', 'Title/Citation', 'Status', 'Stage', 'Last Updated'
        ])
        self.results_table.itemDoubleClicked.connect(self.on_result_double_clicked)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.results_table)

        # Actions
        actions_layout = QHBoxLayout()

        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        actions_layout.addWidget(export_btn)

        actions_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        actions_layout.addWidget(refresh_btn)

        layout.addLayout(actions_layout)

        # Keyboard shortcuts
        self.setup_shortcuts()

        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_filters)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Ctrl+F to focus search
        focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search.activated.connect(self.focus_search)

        # Escape to clear search
        clear_search = QShortcut(QKeySequence("Esc"), self)
        clear_search.activated.connect(self.clear_search)

        # Ctrl+E to focus on errors
        focus_errors = QShortcut(QKeySequence("Ctrl+E"), self)
        focus_errors.activated.connect(self.focus_on_errors)

    def load_data(self):
        """Load all searchable data"""
        try:
            self.all_data = []

            # Get all articles
            if hasattr(self.orchestrator, 'sp_machine'):
                articles = self.orchestrator.sp_machine.sheets_client.get_all_articles()
                for article in articles:
                    self.all_data.append({
                        'type': 'Article',
                        'id': article.get('article_id', ''),
                        'title': article.get('title', ''),
                        'author': article.get('author', ''),
                        'status': article.get('stage', ''),
                        'stage': article.get('stage', ''),
                        'last_updated': article.get('last_updated', ''),
                        'search_text': f"{article.get('article_id', '')} {article.get('title', '')} {article.get('author', '')}",
                        'data': article
                    })

                    # Get sources for each article
                    sources = self.orchestrator.sp_machine.sheets_client.get_sources_for_article(
                        article.get('article_id', '')
                    )
                    for source in sources:
                        self.all_data.append({
                            'type': 'Source',
                            'id': source.get('source_id', ''),
                            'title': source.get('citation', ''),
                            'citation': source.get('citation', ''),
                            'status': source.get('status', ''),
                            'stage': source.get('r2_status', ''),
                            'last_updated': '',
                            'error_message': source.get('error_message', ''),
                            'search_text': f"{source.get('source_id', '')} {source.get('citation', '')}",
                            'data': source
                        })

            logger.info(f"Loaded {len(self.all_data)} searchable items")
            self.apply_filters()

        except Exception as e:
            logger.error(f"Error loading search data: {e}", exc_info=True)

    def on_search_text_changed(self, text: str):
        """Handle search text changes with debouncing"""
        # Debounce: wait 300ms after user stops typing
        self.search_timer.stop()
        self.search_timer.start(300)

    def on_search_return_pressed(self):
        """Handle Enter key in search box"""
        # Jump to first result
        if self.results_table.rowCount() > 0:
            self.results_table.selectRow(0)
            self.results_table.setFocus()

    def apply_filters(self):
        """Apply all active filters"""
        try:
            search_text = self.search_input.text().strip()
            search_type = self.search_type.currentText()

            # Start with all data
            results = self.all_data.copy()

            # Apply type filter
            if search_type != 'All':
                if search_type == 'Errors':
                    results = [r for r in results if r.get('error_message')]
                else:
                    results = [r for r in results if r['type'] == search_type]

            # Apply status filters
            if self.filter_pending.isChecked():
                results = [r for r in results if 'pending' in r.get('status', '').lower()]
            if self.filter_in_progress.isChecked():
                results = [r for r in results if 'progress' in r.get('status', '').lower()]
            if self.filter_completed.isChecked():
                results = [r for r in results if 'complete' in r.get('status', '').lower()]
            if self.filter_errors.isChecked():
                results = [r for r in results if r.get('error_message')]
            if self.filter_review_required.isChecked():
                results = [r for r in results if r.get('requires_review')]

            # Apply search text filter
            if search_text:
                results = self.search_items(results, search_text)

            self.filtered_data = results
            self.update_results_display()

            # Emit filter changed signal
            self.filter_changed.emit({
                'search_text': search_text,
                'search_type': search_type,
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"Error applying filters: {e}", exc_info=True)

    def search_items(self, items: List[Dict], query: str) -> List[Dict]:
        """
        Search items with fuzzy matching

        Args:
            items: List of items to search
            query: Search query

        Returns:
            Filtered list of items
        """
        if not query:
            return items

        results = []

        # Prepare query
        if not self.case_sensitive.isChecked():
            query = query.lower()

        # Regex mode
        if self.regex_checkbox.isChecked():
            try:
                pattern = re.compile(query, re.IGNORECASE if not self.case_sensitive.isChecked() else 0)
                for item in items:
                    search_text = item.get('search_text', '')
                    if pattern.search(search_text):
                        results.append(item)
            except re.error as e:
                logger.warning(f"Invalid regex: {e}")
                return items

        # Fuzzy mode
        elif self.fuzzy_checkbox.isChecked():
            for item in items:
                search_text = item.get('search_text', '')
                if not self.case_sensitive.isChecked():
                    search_text = search_text.lower()

                # Fuzzy match: allow 1-2 character differences per 5 characters
                if self.fuzzy_match(query, search_text):
                    results.append(item)

        # Exact mode
        else:
            for item in items:
                search_text = item.get('search_text', '')
                if not self.case_sensitive.isChecked():
                    search_text = search_text.lower()

                if query in search_text:
                    results.append(item)

        return results

    def fuzzy_match(self, query: str, text: str, threshold: float = 0.8) -> bool:
        """
        Fuzzy string matching using simple character-based algorithm

        Args:
            query: Search query
            text: Text to search in
            threshold: Match threshold (0.0 - 1.0)

        Returns:
            True if fuzzy match
        """
        # Simple substring check first
        if query in text:
            return True

        # Character-based fuzzy matching
        query_chars = list(query)
        text_chars = list(text)

        matches = 0
        text_idx = 0

        for q_char in query_chars:
            found = False
            for i in range(text_idx, len(text_chars)):
                if text_chars[i] == q_char:
                    matches += 1
                    text_idx = i + 1
                    found = True
                    break

        # Calculate match ratio
        ratio = matches / len(query_chars) if query_chars else 0
        return ratio >= threshold

    def update_results_display(self):
        """Update results table with filtered data"""
        try:
            self.results_table.setRowCount(0)
            self.results_table.setRowCount(len(self.filtered_data))

            for row, item in enumerate(self.filtered_data):
                self.results_table.setItem(row, 0, QTableWidgetItem(item.get('type', '')))
                self.results_table.setItem(row, 1, QTableWidgetItem(item.get('id', '')))
                self.results_table.setItem(row, 2, QTableWidgetItem(item.get('title', '')))
                self.results_table.setItem(row, 3, QTableWidgetItem(item.get('status', '')))
                self.results_table.setItem(row, 4, QTableWidgetItem(item.get('stage', '')))
                self.results_table.setItem(row, 5, QTableWidgetItem(item.get('last_updated', '')))

            # Update results count
            self.results_label.setText(f"{len(self.filtered_data)} results")

            # Auto-resize columns
            self.results_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating results display: {e}", exc_info=True)

    def on_result_double_clicked(self, item):
        """Handle double-click on result"""
        try:
            row = item.row()
            if 0 <= row < len(self.filtered_data):
                result = self.filtered_data[row]
                self.result_selected.emit(result)

        except Exception as e:
            logger.error(f"Error handling result click: {e}", exc_info=True)

    def focus_search(self):
        """Focus search input"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def clear_search(self):
        """Clear search input"""
        self.search_input.clear()
        self.search_input.setFocus()

    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.search_type.setCurrentIndex(0)
        self.filter_pending.setChecked(False)
        self.filter_in_progress.setChecked(False)
        self.filter_completed.setChecked(False)
        self.filter_errors.setChecked(False)
        self.filter_review_required.setChecked(False)
        self.fuzzy_checkbox.setChecked(True)
        self.case_sensitive.setChecked(False)
        self.regex_checkbox.setChecked(False)

    def focus_on_errors(self):
        """Quick filter to show only errors"""
        self.clear_filters()
        self.search_type.setCurrentText('Errors')
        self.filter_errors.setChecked(True)

    def export_results(self):
        """Export search results to CSV"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import csv

            if not self.filtered_data:
                return

            # Ask for file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                "search_results.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # Write CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['type', 'id', 'title', 'status', 'stage', 'last_updated'])
                writer.writeheader()

                for item in self.filtered_data:
                    writer.writerow({
                        'type': item.get('type', ''),
                        'id': item.get('id', ''),
                        'title': item.get('title', ''),
                        'status': item.get('status', ''),
                        'stage': item.get('stage', ''),
                        'last_updated': item.get('last_updated', '')
                    })

            logger.info(f"Exported {len(self.filtered_data)} results to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting results: {e}", exc_info=True)
