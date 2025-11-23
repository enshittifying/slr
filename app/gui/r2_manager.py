"""
R2 Manager Widget - Citation validation and review
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QLabel, QMessageBox, QFileDialog, QTextBrowser)
from PyQt6.QtCore import Qt, QUrl
from .progress_widget import ProgressWidget
from .workers import R2WorkerThread
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class R2ManagerWidget(QWidget):
    """R2 Validation management interface"""

    def __init__(self, orchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.current_article_id = None
        self.article_doc_path = None
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

        # Article document selection
        doc_layout = QHBoxLayout()
        doc_layout.addWidget(QLabel("Article Document:"))

        self.doc_path_label = QLabel("No file selected")
        doc_layout.addWidget(self.doc_path_label)

        self.browse_doc_btn = QPushButton("Browse...")
        self.browse_doc_btn.clicked.connect(self.browse_document)
        doc_layout.addWidget(self.browse_doc_btn)

        doc_layout.addStretch()

        layout.addLayout(doc_layout)

        # Status display
        self.status_label = QLabel("Select an article and document to begin")
        layout.addWidget(self.status_label)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start R2 Validation")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        self.view_report_btn = QPushButton("View Review Queue")
        self.view_report_btn.clicked.connect(self.view_review_queue)
        self.view_report_btn.setEnabled(False)
        button_layout.addWidget(self.view_report_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Progress widget
        self.progress = ProgressWidget("R2 Validation Progress")
        layout.addWidget(self.progress)

        # Review queue preview
        self.review_browser = QTextBrowser()
        self.review_browser.setMaximumHeight(300)
        self.review_browser.setVisible(False)
        layout.addWidget(self.review_browser)

        self.setLayout(layout)

        # Load articles on startup
        self.load_articles()

    def load_articles(self):
        """Load articles from Google Sheets"""
        try:
            self.article_combo.clear()

            articles = self.orchestrator.sheets.get_all_articles()

            # Filter to articles that have completed R1
            r1_complete_articles = [a for a in articles
                                   if 'r1_complete' in a['stage'].lower()]

            for article in r1_complete_articles:
                display_text = f"{article['volume_issue']} - {article['author']} - {article['title'][:30]}"
                self.article_combo.addItem(display_text, article['article_id'])

            logger.info(f"Loaded {len(r1_complete_articles)} R1-complete articles")

            if len(r1_complete_articles) == 0:
                self.status_label.setText("No articles ready for R2 (R1 must be complete first)")

        except Exception as e:
            logger.error(f"Error loading articles: {e}", exc_info=True)
            QMessageBox.critical(self, "Error",
                               f"Failed to load articles: {str(e)}")

    def on_article_changed(self, index):
        """Handle article selection change"""
        if index < 0:
            return

        self.current_article_id = self.article_combo.itemData(index)

        # Update status
        status = self.orchestrator.get_pipeline_status(self.current_article_id)
        self.status_label.setText(
            f"Stage: {status['current_stage']} | "
            f"Sources: {status['sources_total']}"
        )

        self.update_start_button()

    def browse_document(self):
        """Browse for article Word document"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Article Document",
            "",
            "Word Documents (*.docx)"
        )

        if file_path:
            self.article_doc_path = file_path
            self.doc_path_label.setText(Path(file_path).name)
            self.update_start_button()

            logger.info(f"Selected article document: {file_path}")

    def update_start_button(self):
        """Enable start button if both article and document are selected"""
        self.start_btn.setEnabled(
            self.current_article_id is not None and
            self.article_doc_path is not None
        )

    def start_processing(self):
        """Start R2 processing"""
        if not self.current_article_id or not self.article_doc_path:
            QMessageBox.warning(self, "Warning",
                              "Please select both an article and document")
            return

        # Confirm start
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Start R2 Validation for article {self.current_article_id}?\n\n"
            "This will use LLM to validate all citations.\n"
            "Note: This may incur API costs.",
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
            self.review_browser.setVisible(False)

            # Create and start worker thread
            self.worker = R2WorkerThread(
                self.orchestrator,
                self.current_article_id,
                self.article_doc_path
            )
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.finished_with_result.connect(self.on_processing_finished)
            self.worker.error_occurred.connect(self.on_processing_error)
            self.worker.start()

            logger.info(f"Started R2 processing for article {self.current_article_id}")

        except Exception as e:
            logger.error(f"Error starting R2: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def stop_processing(self):
        """Stop R2 processing"""
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
        self.progress.set_complete(
            result['citations_checked'] - result['issues_found'],
            result['issues_found']
        )

        self.view_report_btn.setEnabled(True)

        QMessageBox.information(
            self,
            "Complete",
            f"R2 Validation complete!\n"
            f"Citations checked: {result['citations_checked']}\n"
            f"Issues found: {result['issues_found']}\n\n"
            f"Click 'View Review Queue' to see items requiring review."
        )

        logger.info(f"R2 processing finished: {result}")

    def on_processing_error(self, error_message):
        """Handle processing error"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.set_processing(False)
        self.progress.set_error(error_message)

        QMessageBox.critical(self, "Error", f"Processing failed: {error_message}")

        logger.error(f"R2 processing error: {error_message}")

    def view_review_queue(self):
        """View the review queue HTML report"""
        try:
            # Find the review queue HTML file
            cache_dir = Path("cache/r2")
            html_file = cache_dir / f"{self.current_article_id}_review_queue.html"

            if html_file.exists():
                # Load HTML into browser
                with open(html_file, 'r') as f:
                    html_content = f.read()

                self.review_browser.setHtml(html_content)
                self.review_browser.setVisible(True)

                logger.info(f"Displayed review queue for {self.current_article_id}")

            else:
                QMessageBox.warning(self, "Not Found",
                                  "Review queue report not found. Please run R2 validation first.")

        except Exception as e:
            logger.error(f"Error viewing review queue: {e}", exc_info=True)
            QMessageBox.critical(self, "Error",
                               f"Failed to load review queue: {str(e)}")
