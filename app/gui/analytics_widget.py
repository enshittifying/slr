"""
Analytics Dashboard Widget - Real-time insights and metrics
SUPERCHARGED: Live charts, cost tracking, performance monitoring
"""
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QTabWidget, QProgressBar, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricCard(QFrame):
    """Card widget for displaying a single metric"""

    def __init__(self, title: str, value: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(False)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #666666;")
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        layout.addWidget(self.value_label)

        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999999; font-size: 9pt;")
            layout.addWidget(subtitle_label)

        layout.addStretch()

    def update_value(self, value: str):
        """Update metric value"""
        self.value_label.setText(value)


class AnalyticsWidget(QWidget):
    """
    Analytics dashboard widget

    Features:
    - Real-time metrics (validations, cost, performance)
    - Live charts (trends over time)
    - Cost breakdown by provider/model
    - Performance analytics (throughput, avg times)
    - Budget alerts and warnings
    - Optimization recommendations
    - Export capabilities
    """

    refresh_requested = pyqtSignal()

    def __init__(self, analytics_engine, cost_optimizer, parent=None):
        super().__init__(parent)
        self.analytics = analytics_engine
        self.optimizer = cost_optimizer
        self.metric_cards = {}

        self.setup_ui()
        self.start_auto_refresh()

    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Analytics Dashboard")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)

        # Export button
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        # Last updated
        self.last_updated_label = QLabel("Last updated: Never")
        self.last_updated_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(self.last_updated_label)

        # Tabs for different analytics views
        tabs = QTabWidget()

        # Overview tab
        overview_tab = self.create_overview_tab()
        tabs.addTab(overview_tab, "Overview")

        # Cost tab
        cost_tab = self.create_cost_tab()
        tabs.addTab(cost_tab, "Cost Analysis")

        # Performance tab
        performance_tab = self.create_performance_tab()
        tabs.addTab(performance_tab, "Performance")

        # Optimization tab
        optimization_tab = self.create_optimization_tab()
        tabs.addTab(optimization_tab, "Optimization")

        layout.addWidget(tabs)

    def create_overview_tab(self) -> QWidget:
        """Create overview tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Metric cards
        cards_layout = QHBoxLayout()

        # Total validations card
        self.metric_cards['total_validations'] = MetricCard(
            "Total Validations",
            "0",
            "All time"
        )
        cards_layout.addWidget(self.metric_cards['total_validations'])

        # Issues found card
        self.metric_cards['issues_found'] = MetricCard(
            "Issues Found",
            "0",
            "Format + Support"
        )
        cards_layout.addWidget(self.metric_cards['issues_found'])

        # Review queue card
        self.metric_cards['review_queue'] = MetricCard(
            "Review Queue",
            "0",
            "Pending review"
        )
        cards_layout.addWidget(self.metric_cards['review_queue'])

        # Total cost card
        self.metric_cards['total_cost'] = MetricCard(
            "Total Cost",
            "$0.00",
            "Last 30 days"
        )
        cards_layout.addWidget(self.metric_cards['total_cost'])

        layout.addLayout(cards_layout)

        # Summary table
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QVBoxLayout()
        summary_group.setLayout(summary_layout)

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.summary_table.setAlternatingRowColors(True)
        summary_layout.addWidget(self.summary_table)

        layout.addWidget(summary_group)

        return tab

    def create_cost_tab(self) -> QWidget:
        """Create cost analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Cost metric cards
        cards_layout = QHBoxLayout()

        self.metric_cards['api_calls'] = MetricCard(
            "API Calls",
            "0",
            "Last 30 days"
        )
        cards_layout.addWidget(self.metric_cards['api_calls'])

        self.metric_cards['tokens_used'] = MetricCard(
            "Tokens Used",
            "0",
            "Input + Output"
        )
        cards_layout.addWidget(self.metric_cards['tokens_used'])

        self.metric_cards['cost_per_article'] = MetricCard(
            "Cost/Article",
            "$0.00",
            "Average"
        )
        cards_layout.addWidget(self.metric_cards['cost_per_article'])

        layout.addLayout(cards_layout)

        # Cost breakdown
        breakdown_group = QGroupBox("Cost Breakdown")
        breakdown_layout = QVBoxLayout()
        breakdown_group.setLayout(breakdown_layout)

        self.cost_breakdown_table = QTableWidget()
        self.cost_breakdown_table.setColumnCount(3)
        self.cost_breakdown_table.setHorizontalHeaderLabels(['Category', 'Cost', 'Percentage'])
        self.cost_breakdown_table.setAlternatingRowColors(True)
        breakdown_layout.addWidget(self.cost_breakdown_table)

        layout.addWidget(breakdown_group)

        # Budget alerts
        alerts_group = QGroupBox("Budget Alerts")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)

        self.budget_alerts_label = QLabel("No budget alerts")
        alerts_layout.addWidget(self.budget_alerts_label)

        layout.addWidget(alerts_group)

        return tab

    def create_performance_tab(self) -> QWidget:
        """Create performance tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Performance cards
        cards_layout = QHBoxLayout()

        self.metric_cards['avg_sp_time'] = MetricCard(
            "Avg SP Time",
            "0s",
            "Source Pull"
        )
        cards_layout.addWidget(self.metric_cards['avg_sp_time'])

        self.metric_cards['avg_r1_time'] = MetricCard(
            "Avg R1 Time",
            "0s",
            "Redboxing"
        )
        cards_layout.addWidget(self.metric_cards['avg_r1_time'])

        self.metric_cards['avg_r2_time'] = MetricCard(
            "Avg R2 Time",
            "0s",
            "Validation"
        )
        cards_layout.addWidget(self.metric_cards['avg_r2_time'])

        self.metric_cards['articles_per_hour'] = MetricCard(
            "Throughput",
            "0",
            "Articles/hour"
        )
        cards_layout.addWidget(self.metric_cards['articles_per_hour'])

        layout.addLayout(cards_layout)

        # Performance metrics table
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout()
        metrics_group.setLayout(metrics_layout)

        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(2)
        self.performance_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.performance_table.setAlternatingRowColors(True)
        metrics_layout.addWidget(self.performance_table)

        layout.addWidget(metrics_group)

        return tab

    def create_optimization_tab(self) -> QWidget:
        """Create optimization tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Projected savings card
        savings_layout = QHBoxLayout()

        self.metric_cards['projected_savings'] = MetricCard(
            "Projected Savings",
            "$0.00",
            "Monthly"
        )
        savings_layout.addWidget(self.metric_cards['projected_savings'])

        self.metric_cards['optimization_opportunities'] = MetricCard(
            "Opportunities",
            "0",
            "Available"
        )
        savings_layout.addWidget(self.metric_cards['optimization_opportunities'])

        layout.addLayout(savings_layout)

        # Recommendations
        recommendations_group = QGroupBox("Optimization Recommendations")
        recommendations_layout = QVBoxLayout()
        recommendations_group.setLayout(recommendations_layout)

        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(4)
        self.recommendations_table.setHorizontalHeaderLabels([
            'Priority', 'Recommendation', 'Savings', 'Effort'
        ])
        self.recommendations_table.setAlternatingRowColors(True)
        recommendations_layout.addWidget(self.recommendations_table)

        layout.addWidget(recommendations_group)

        # Apply recommendations button
        apply_btn = QPushButton("Apply Selected Recommendations")
        apply_btn.clicked.connect(self.apply_recommendations)
        layout.addWidget(apply_btn)

        return tab

    def refresh_data(self):
        """Refresh all analytics data"""
        try:
            logger.info("Refreshing analytics data...")

            # Get metrics
            validation_metrics = self.analytics.compute_validation_metrics()
            performance_metrics = self.analytics.compute_performance_metrics()
            cost_metrics = self.analytics.compute_cost_metrics()

            # Update overview cards
            self.metric_cards['total_validations'].update_value(str(validation_metrics.total_validations))
            self.metric_cards['issues_found'].update_value(
                str(validation_metrics.format_issues_found + validation_metrics.support_issues_found)
            )
            self.metric_cards['review_queue'].update_value(str(validation_metrics.review_queue_size))
            self.metric_cards['total_cost'].update_value(f"${cost_metrics.total_cost_usd:.2f}")

            # Update cost cards
            self.metric_cards['api_calls'].update_value(str(cost_metrics.total_api_calls))
            self.metric_cards['tokens_used'].update_value(f"{cost_metrics.total_tokens_used:,}")
            self.metric_cards['cost_per_article'].update_value(f"${cost_metrics.avg_cost_per_article:.2f}")

            # Update performance cards
            self.metric_cards['avg_sp_time'].update_value(f"{performance_metrics.avg_sp_time:.1f}s")
            self.metric_cards['avg_r1_time'].update_value(f"{performance_metrics.avg_r1_time:.1f}s")
            self.metric_cards['avg_r2_time'].update_value(f"{performance_metrics.avg_r2_time:.1f}s")
            self.metric_cards['articles_per_hour'].update_value(f"{performance_metrics.articles_per_hour:.1f}")

            # Update summary table
            self.update_summary_table(validation_metrics, performance_metrics, cost_metrics)

            # Update cost breakdown
            self.update_cost_breakdown(cost_metrics)

            # Update budget alerts
            self.update_budget_alerts()

            # Update performance table
            self.update_performance_table(performance_metrics)

            # Update optimization recommendations
            self.update_optimization_recommendations()

            # Update last updated timestamp
            self.last_updated_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            logger.info("Analytics data refreshed successfully")

        except Exception as e:
            logger.error(f"Error refreshing analytics: {e}", exc_info=True)

    def update_summary_table(self, validation_metrics, performance_metrics, cost_metrics):
        """Update summary statistics table"""
        try:
            rows = [
                ('Total Validations', str(validation_metrics.total_validations)),
                ('Format Issues Found', str(validation_metrics.format_issues_found)),
                ('Support Issues Found', str(validation_metrics.support_issues_found)),
                ('Average Confidence', f"{validation_metrics.average_confidence:.1f}%"),
                ('Auto Approved', str(validation_metrics.auto_approved)),
                ('Manual Review Required', str(validation_metrics.manual_review_required)),
                ('Average Processing Time', f"{performance_metrics.avg_full_pipeline_time:.1f}s"),
                ('Total Cost', f"${cost_metrics.total_cost_usd:.2f}"),
            ]

            self.summary_table.setRowCount(len(rows))
            for i, (metric, value) in enumerate(rows):
                self.summary_table.setItem(i, 0, QTableWidgetItem(metric))
                self.summary_table.setItem(i, 1, QTableWidgetItem(value))

            self.summary_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating summary table: {e}", exc_info=True)

    def update_cost_breakdown(self, cost_metrics):
        """Update cost breakdown table"""
        try:
            rows = [
                ('OpenAI', f"${cost_metrics.openai_cost:.2f}", f"{(cost_metrics.openai_cost / max(cost_metrics.total_cost_usd, 1) * 100):.1f}%"),
                ('Anthropic', f"${cost_metrics.anthropic_cost:.2f}", f"{(cost_metrics.anthropic_cost / max(cost_metrics.total_cost_usd, 1) * 100):.1f}%"),
            ]

            self.cost_breakdown_table.setRowCount(len(rows))
            for i, (category, cost, percentage) in enumerate(rows):
                self.cost_breakdown_table.setItem(i, 0, QTableWidgetItem(category))
                self.cost_breakdown_table.setItem(i, 1, QTableWidgetItem(cost))
                self.cost_breakdown_table.setItem(i, 2, QTableWidgetItem(percentage))

            self.cost_breakdown_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating cost breakdown: {e}", exc_info=True)

    def update_budget_alerts(self):
        """Update budget alerts"""
        try:
            alerts = self.analytics.check_budget_alerts(
                daily_budget=100.0,
                monthly_budget=2000.0
            )

            if alerts:
                alert_text = "<ul>"
                for alert in alerts:
                    severity = alert['severity']
                    message = alert['message']
                    color = 'orange' if severity == 'warning' else 'red'
                    alert_text += f"<li style='color: {color};'><b>{severity.upper()}:</b> {message}</li>"
                alert_text += "</ul>"
                self.budget_alerts_label.setText(alert_text)
            else:
                self.budget_alerts_label.setText("✓ No budget alerts")

        except Exception as e:
            logger.error(f"Error updating budget alerts: {e}", exc_info=True)

    def update_performance_table(self, performance_metrics):
        """Update performance metrics table"""
        try:
            rows = [
                ('Average SP Time', f"{performance_metrics.avg_sp_time:.1f} seconds"),
                ('Average R1 Time', f"{performance_metrics.avg_r1_time:.1f} seconds"),
                ('Average R2 Time', f"{performance_metrics.avg_r2_time:.1f} seconds"),
                ('Full Pipeline Time', f"{performance_metrics.avg_full_pipeline_time:.1f} seconds"),
                ('Articles per Hour', f"{performance_metrics.articles_per_hour:.1f}"),
            ]

            self.performance_table.setRowCount(len(rows))
            for i, (metric, value) in enumerate(rows):
                self.performance_table.setItem(i, 0, QTableWidgetItem(metric))
                self.performance_table.setItem(i, 1, QTableWidgetItem(value))

            self.performance_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating performance table: {e}", exc_info=True)

    def update_optimization_recommendations(self):
        """Update optimization recommendations"""
        try:
            recommendations = self.optimizer.get_optimization_recommendations()

            # Update cards
            total_savings = sum(r.potential_savings_usd for r in recommendations)
            self.metric_cards['projected_savings'].update_value(f"${total_savings:.2f}")
            self.metric_cards['optimization_opportunities'].update_value(str(len(recommendations)))

            # Update table
            self.recommendations_table.setRowCount(len(recommendations))
            for i, rec in enumerate(recommendations):
                self.recommendations_table.setItem(i, 0, QTableWidgetItem(str(rec.priority)))
                self.recommendations_table.setItem(i, 1, QTableWidgetItem(rec.title))
                self.recommendations_table.setItem(i, 2, QTableWidgetItem(f"${rec.potential_savings_usd:.2f}"))
                self.recommendations_table.setItem(i, 3, QTableWidgetItem(rec.effort))

            self.recommendations_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating optimization recommendations: {e}", exc_info=True)

    def apply_recommendations(self):
        """Apply selected optimization recommendations"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Apply Recommendations",
            "Optimization recommendations would be applied here.\n\n"
            "This feature requires integration with the main application settings."
        )

    def export_report(self):
        """Export analytics report"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Analytics Report",
                f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )

            if file_path:
                self.analytics.export_report(file_path, format='json', include_trends=True)
                logger.info(f"Exported analytics report to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting report: {e}", exc_info=True)

    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Initial refresh
        self.refresh_data()
