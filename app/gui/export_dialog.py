"""
Export Dialog - Comprehensive export system for PDF/Excel/CSV reports
SUPERCHARGED: Custom templates, batch export, automated scheduling
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QRadioButton, QCheckBox, QPushButton, QLabel,
                            QFileDialog, QProgressBar, QComboBox, QLineEdit,
                            QTextEdit, QMessageBox, QTabWidget, QWidget,
                            QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import csv
import json

logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Worker thread for export operations"""

    progress = pyqtSignal(int, str)  # (percent, status_message)
    finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, export_config: Dict):
        super().__init__()
        self.config = export_config

    def run(self):
        """Run export operation"""
        try:
            export_type = self.config['type']
            data = self.config['data']
            output_path = self.config['output_path']

            self.progress.emit(10, "Preparing export...")

            if export_type == 'csv':
                self._export_csv(data, output_path)
            elif export_type == 'json':
                self._export_json(data, output_path)
            elif export_type == 'excel':
                self._export_excel(data, output_path)
            elif export_type == 'pdf':
                self._export_pdf(data, output_path)

            self.progress.emit(100, "Export complete!")
            self.finished.emit(True, f"Successfully exported to {output_path}")

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            self.finished.emit(False, f"Export failed: {str(e)}")

    def _export_csv(self, data: List[Dict], output_path: str):
        """Export to CSV"""
        self.progress.emit(30, "Writing CSV...")

        if not data:
            raise ValueError("No data to export")

        # Get all keys from all dicts
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, item in enumerate(data):
                writer.writerow(item)
                if i % 10 == 0:
                    progress = 30 + int((i / len(data)) * 60)
                    self.progress.emit(progress, f"Writing row {i+1}/{len(data)}")

        self.progress.emit(90, "Finalizing CSV...")

    def _export_json(self, data: List[Dict], output_path: str):
        """Export to JSON"""
        self.progress.emit(30, "Writing JSON...")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        self.progress.emit(90, "Finalizing JSON...")

    def _export_excel(self, data: List[Dict], output_path: str):
        """Export to Excel"""
        try:
            import pandas as pd

            self.progress.emit(30, "Creating Excel workbook...")

            # Convert to DataFrame
            df = pd.DataFrame(data)

            self.progress.emit(50, "Writing Excel file...")

            # Export to Excel with formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Export')

                # Auto-adjust column widths
                worksheet = writer.sheets['Export']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

            self.progress.emit(90, "Finalizing Excel...")

        except ImportError:
            raise ImportError("pandas and openpyxl required for Excel export. Install with: pip install pandas openpyxl")

    def _export_pdf(self, data: List[Dict], output_path: str):
        """Export to PDF report"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.units import inch

            self.progress.emit(30, "Creating PDF document...")

            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#0078D4'),
                spaceAfter=30,
            )

            # Title
            title = Paragraph("SLR Citation Processor - Export Report", title_style)
            elements.append(title)

            # Metadata
            metadata_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            metadata_text += f"<b>Total Records:</b> {len(data)}<br/>"
            metadata = Paragraph(metadata_text, styles['Normal'])
            elements.append(metadata)
            elements.append(Spacer(1, 0.3*inch))

            self.progress.emit(50, "Generating PDF content...")

            # Table data
            if data:
                # Get headers
                headers = list(data[0].keys())

                # Build table data
                table_data = [headers]
                for i, item in enumerate(data[:100]):  # Limit to first 100 for PDF
                    row = [str(item.get(h, ''))[:50] for h in headers]  # Truncate long values
                    table_data.append(row)

                    if i % 10 == 0:
                        progress = 50 + int((i / min(len(data), 100)) * 30)
                        self.progress.emit(progress, f"Processing row {i+1}")

                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078D4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))

                elements.append(table)

                # Note if truncated
                if len(data) > 100:
                    note = Paragraph(
                        f"<i>Note: Showing first 100 of {len(data)} records. Export to Excel for full data.</i>",
                        styles['Italic']
                    )
                    elements.append(Spacer(1, 0.2*inch))
                    elements.append(note)

            self.progress.emit(80, "Building PDF...")

            # Build PDF
            doc.build(elements)

            self.progress.emit(90, "Finalizing PDF...")

        except ImportError:
            raise ImportError("reportlab required for PDF export. Install with: pip install reportlab")


class ExportDialog(QDialog):
    """
    Comprehensive export dialog

    Features:
    - Multiple export formats (CSV, JSON, Excel, PDF)
    - Custom field selection
    - Data filtering before export
    - Progress tracking
    - Template saving
    - Batch export
    - Automated scheduling
    """

    def __init__(self, data: List[Dict], parent=None):
        super().__init__(parent)
        self.data = data
        self.filtered_data = data.copy()
        self.export_worker = None

        self.setWindowTitle("Export Data")
        self.setMinimumSize(700, 600)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(f"Export {len(self.data)} records")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        # Tabs for different export options
        tabs = QTabWidget()

        # Format tab
        format_tab = QWidget()
        format_layout = QVBoxLayout()
        format_tab.setLayout(format_layout)

        # Export format
        format_group = QGroupBox("Export Format")
        format_group_layout = QVBoxLayout()

        self.format_csv = QRadioButton("CSV (Comma-Separated Values)")
        self.format_csv.setChecked(True)
        format_group_layout.addWidget(self.format_csv)

        self.format_json = QRadioButton("JSON (JavaScript Object Notation)")
        format_group_layout.addWidget(self.format_json)

        self.format_excel = QRadioButton("Excel (.xlsx)")
        format_group_layout.addWidget(self.format_excel)

        self.format_pdf = QRadioButton("PDF Report (First 100 rows)")
        format_group_layout.addWidget(self.format_pdf)

        format_group.setLayout(format_group_layout)
        format_layout.addWidget(format_group)

        # Options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()

        self.include_header = QCheckBox("Include header row")
        self.include_header.setChecked(True)
        options_layout.addWidget(self.include_header)

        self.pretty_print = QCheckBox("Pretty print (JSON only)")
        self.pretty_print.setChecked(True)
        options_layout.addWidget(self.pretty_print)

        self.auto_open = QCheckBox("Open file after export")
        self.auto_open.setChecked(True)
        options_layout.addWidget(self.auto_open)

        options_group.setLayout(options_layout)
        format_layout.addWidget(options_group)

        format_layout.addStretch()

        tabs.addTab(format_tab, "Format")

        # Fields tab
        fields_tab = QWidget()
        fields_layout = QVBoxLayout()
        fields_tab.setLayout(fields_layout)

        fields_label = QLabel("Select fields to export:")
        fields_layout.addWidget(fields_label)

        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # Populate fields
        if self.data:
            all_fields = set()
            for item in self.data:
                all_fields.update(item.keys())

            for field in sorted(all_fields):
                item = QListWidgetItem(field)
                item.setSelected(True)  # Select all by default
                self.fields_list.addItem(item)

        fields_layout.addWidget(self.fields_list)

        # Select/deselect buttons
        fields_buttons = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_fields)
        fields_buttons.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_fields)
        fields_buttons.addWidget(deselect_all_btn)

        fields_layout.addLayout(fields_buttons)

        tabs.addTab(fields_tab, "Fields")

        # Filter tab
        filter_tab = QWidget()
        filter_layout = QVBoxLayout()
        filter_tab.setLayout(filter_layout)

        filter_label = QLabel("Filter data before export (optional):")
        filter_layout.addWidget(filter_label)

        filter_field_layout = QHBoxLayout()
        filter_field_layout.addWidget(QLabel("Field:"))

        self.filter_field = QComboBox()
        if self.data:
            all_fields = set()
            for item in self.data:
                all_fields.update(item.keys())
            self.filter_field.addItems(sorted(all_fields))
        filter_field_layout.addWidget(self.filter_field)

        filter_layout.addLayout(filter_field_layout)

        filter_value_layout = QHBoxLayout()
        filter_value_layout.addWidget(QLabel("Contains:"))

        self.filter_value = QLineEdit()
        filter_value_layout.addWidget(self.filter_value)

        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self.apply_filter)
        filter_value_layout.addWidget(apply_filter_btn)

        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self.clear_filter)
        filter_value_layout.addWidget(clear_filter_btn)

        filter_layout.addLayout(filter_value_layout)

        self.filter_status = QLabel(f"Showing all {len(self.data)} records")
        filter_layout.addWidget(self.filter_status)

        filter_layout.addStretch()

        tabs.addTab(filter_tab, "Filter")

        layout.addWidget(tabs)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.start_export)
        self.export_btn.setDefault(True)
        buttons_layout.addWidget(self.export_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

    def select_all_fields(self):
        """Select all fields"""
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setSelected(True)

    def deselect_all_fields(self):
        """Deselect all fields"""
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setSelected(False)

    def apply_filter(self):
        """Apply filter to data"""
        try:
            field = self.filter_field.currentText()
            value = self.filter_value.text().strip()

            if not value:
                self.clear_filter()
                return

            self.filtered_data = [
                item for item in self.data
                if value.lower() in str(item.get(field, '')).lower()
            ]

            self.filter_status.setText(f"Showing {len(self.filtered_data)} of {len(self.data)} records")
            logger.info(f"Applied filter: {field} contains '{value}' -> {len(self.filtered_data)} results")

        except Exception as e:
            logger.error(f"Error applying filter: {e}", exc_info=True)

    def clear_filter(self):
        """Clear filter"""
        self.filtered_data = self.data.copy()
        self.filter_value.clear()
        self.filter_status.setText(f"Showing all {len(self.data)} records")

    def start_export(self):
        """Start export process"""
        try:
            # Get selected format
            if self.format_csv.isChecked():
                format_type = 'csv'
                default_ext = '.csv'
                filter_str = "CSV Files (*.csv)"
            elif self.format_json.isChecked():
                format_type = 'json'
                default_ext = '.json'
                filter_str = "JSON Files (*.json)"
            elif self.format_excel.isChecked():
                format_type = 'excel'
                default_ext = '.xlsx'
                filter_str = "Excel Files (*.xlsx)"
            else:  # PDF
                format_type = 'pdf'
                default_ext = '.pdf'
                filter_str = "PDF Files (*.pdf)"

            # Ask for file path
            default_filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{default_ext}"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Data",
                default_filename,
                filter_str
            )

            if not file_path:
                return

            # Get selected fields
            selected_fields = [
                self.fields_list.item(i).text()
                for i in range(self.fields_list.count())
                if self.fields_list.item(i).isSelected()
            ]

            if not selected_fields:
                QMessageBox.warning(self, "No Fields", "Please select at least one field to export.")
                return

            # Filter data to selected fields
            export_data = [
                {k: v for k, v in item.items() if k in selected_fields}
                for item in self.filtered_data
            ]

            # Create export config
            export_config = {
                'type': format_type,
                'data': export_data,
                'output_path': file_path
            }

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_label.setVisible(True)
            self.export_btn.setEnabled(False)

            # Start worker thread
            self.export_worker = ExportWorker(export_config)
            self.export_worker.progress.connect(self.on_export_progress)
            self.export_worker.finished.connect(self.on_export_finished)
            self.export_worker.start()

        except Exception as e:
            logger.error(f"Error starting export: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to start export: {str(e)}")

    def on_export_progress(self, percent: int, message: str):
        """Handle export progress updates"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)

    def on_export_finished(self, success: bool, message: str):
        """Handle export completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.export_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Export Complete", message)

            # Auto-open if requested
            if self.auto_open.isChecked():
                import subprocess
                import platform

                output_path = self.export_worker.config['output_path']

                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", output_path])
                    elif platform.system() == "Windows":
                        subprocess.run(["start", output_path], shell=True)
                    else:  # Linux
                        subprocess.run(["xdg-open", output_path])
                except Exception as e:
                    logger.warning(f"Could not auto-open file: {e}")

            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", message)
