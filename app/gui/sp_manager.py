"""
Source Pull Manager Widget
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QLabel, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from .progress_widget import ProgressWidget
from .workers import SPWorkerThread
import logging

logger = logging.getLogger(__name__)


class SPManagerWidget(QWidget):
    """Source Pull management interface"""

    def __init__(self, orchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.current_article_id = None
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout()

        # Article selection
        article_layout = QHBoxLayout()
        article_layout.addWidget(QLabel("Article:"))

        self.article_combo = QComboBox()
        self.article_combo.currentIndexChanged.connect(self.on_article_changed)
        article_layout.addWidget(self.article_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_articles)
        article_layout.addWidget(self.refresh_btn)

        article_layout.addStretch()

        layout.addLayout(article_layout)

        # Status display
        self.status_label = QLabel("Select an article to begin")
        layout.addWidget(self.status_label)

        # Sources table
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(5)
        self.sources_table.setHorizontalHeaderLabels([
            "Source ID", "Footnote", "Citation", "Status", "Link"
        ])
        self.sources_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sources_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sources_table)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Source Pull")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Progress widget
        self.progress = ProgressWidget("Source Pull Progress")
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Load articles on startup
        self.load_articles()

    def load_articles(self):
        """Load articles from Google Sheets"""
        try:
            self.article_combo.clear()

            articles = self.orchestrator.sheets.get_all_articles()

            for article in articles:
                display_text = f"{article['volume_issue']} - {article['author']} - {article['title'][:30]}"
                self.article_combo.addItem(display_text, article['article_id'])

            logger.info(f"Loaded {len(articles)} articles")

        except Exception as e:
            logger.error(f"Error loading articles: {e}", exc_info=True)
            QMessageBox.critical(self, "Error",
                               f"Failed to load articles: {str(e)}")

    def on_article_changed(self, index):
        """Handle article selection change"""
        if index < 0:
            return

        self.current_article_id = self.article_combo.itemData(index)
        self.load_sources()

        # Update status
        status = self.orchestrator.get_pipeline_status(self.current_article_id)
        self.status_label.setText(
            f"Stage: {status['current_stage']} | "
            f"Sources: {status['sources_completed']}/{status['sources_total']} | "
            f"Cached: {status['sp_cached']}"
        )

        self.start_btn.setEnabled(True)

    def load_sources(self):
        """Load sources for selected article"""
        if not self.current_article_id:
            return

        try:
            sources = self.orchestrator.sheets.get_sources_for_article(
                self.current_article_id
            )

            self.sources_table.setRowCount(len(sources))

            for row, source in enumerate(sources):
                self.sources_table.setItem(row, 0,
                    QTableWidgetItem(source['source_id']))
                self.sources_table.setItem(row, 1,
                    QTableWidgetItem(source['footnote_num']))
                self.sources_table.setItem(row, 2,
                    QTableWidgetItem(source['citation'][:60]))
                self.sources_table.setItem(row, 3,
                    QTableWidgetItem(source['status']))
                self.sources_table.setItem(row, 4,
                    QTableWidgetItem(source['drive_link'][:40] if source['drive_link'] else ''))

            self.sources_table.resizeColumnsToContents()

            logger.info(f"Loaded {len(sources)} sources for article {self.current_article_id}")

        except Exception as e:
            logger.error(f"Error loading sources: {e}", exc_info=True)
            QMessageBox.critical(self, "Error",
                               f"Failed to load sources: {str(e)}")

    def start_processing(self):
        """Start SP processing"""
        if not self.current_article_id:
            QMessageBox.warning(self, "Warning", "Please select an article first")
            return

        # Confirm start
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Start Source Pull for article {self.current_article_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Disable start button, enable stop button
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress.reset()
            self.progress.set_processing(True)

            # Create and start worker thread
            self.worker = SPWorkerThread(self.orchestrator, self.current_article_id)
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.finished_with_result.connect(self.on_processing_finished)
            self.worker.error_occurred.connect(self.on_processing_error)
            self.worker.start()

            logger.info(f"Started SP processing for article {self.current_article_id}")

        except Exception as e:
            logger.error(f"Error starting SP: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def stop_processing(self):
        """Stop SP processing"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm",
                "Stop processing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                self.progress.set_status("Stopped by user")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)

    def on_progress_updated(self, current, total, message):
        """Handle progress update from worker"""
        self.progress.update_progress(current, total, message)

    def on_processing_finished(self, result):
        """Handle processing completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.set_processing(False)
        self.progress.set_complete(result['success_count'], result['fail_count'])

        # Reload sources to show updated status
        self.load_sources()

        QMessageBox.information(
            self,
            "Complete",
            f"Source Pull complete!\n"
            f"Success: {result['success_count']}\n"
            f"Failed: {result['fail_count']}"
        )

        logger.info(f"SP processing finished: {result}")

    def on_processing_error(self, error_message):
        """Handle processing error"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.set_processing(False)
        self.progress.set_error(error_message)

        QMessageBox.critical(self, "Error", f"Processing failed: {error_message}")

        logger.error(f"SP processing error: {error_message}")
