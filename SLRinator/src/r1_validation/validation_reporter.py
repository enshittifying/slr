"""
Validation Reporter for R1
Generates comprehensive validation reports for R1 cite checking
"""
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationReporter:
    """Generate comprehensive R1 validation reports."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path.cwd() / "output" / "r1_validation"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.human_review_queue = []

    def generate_report(self, citations: List[Dict[str, Any]], metadata: Dict = None) -> Dict:
        """
        Generate comprehensive validation report.

        Args:
            citations: List of citation validation results
            metadata: Additional metadata (article info, run info, etc.)

        Returns:
            Report dictionary
        """
        # Calculate statistics
        total_citations = len(citations)
        citations_validated = sum(1 for c in citations if c.get('validation_result'))
        citations_correct = sum(1 for c in citations
                               if c.get('validation_result', {}).get('validation', {}).get('is_correct'))
        citations_with_errors = citations_validated - citations_correct

        quotes_checked = sum(1 for c in citations if c.get('quote_verification'))
        quotes_accurate = sum(1 for c in citations
                             if c.get('quote_verification', {}).get('accurate'))

        support_checks = sum(1 for c in citations if c.get('support_check'))
        support_confirmed = sum(1 for c in citations
                               if c.get('support_check', {}).get('analysis', {}).get('support_level') == 'yes')

        # Build report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "slr_system": "R1 Cite Checking",
                "version": "1.0.0",
                **(metadata or {})
            },

            "validation_summary": {
                "total_citations": total_citations,
                "citations_validated": citations_validated,
                "citations_correct": citations_correct,
                "citations_with_errors": citations_with_errors,
                "accuracy_rate": f"{(citations_correct / citations_validated * 100):.1f}%" if citations_validated else "N/A",

                "quotes_checked": quotes_checked,
                "quotes_accurate": quotes_accurate,
                "quote_accuracy_rate": f"{(quotes_accurate / quotes_checked * 100):.1f}%" if quotes_checked else "N/A",

                "support_checks_performed": support_checks,
                "support_confirmed": support_confirmed,
                "support_confirmation_rate": f"{(support_confirmed / support_checks * 100):.1f}%" if support_checks else "N/A"
            },

            "citations": citations,

            "human_review_queue": self.human_review_queue,

            "cost_analysis": self._calculate_costs(citations)
        }

        return report

    def _calculate_costs(self, citations: List[Dict]) -> Dict:
        """Calculate total API costs."""
        total_tokens = 0
        total_cost = 0.0

        for cit in citations:
            if cit.get('validation_result'):
                val = cit['validation_result'].get('validation', {})
                total_tokens += val.get('gpt_tokens', 0)
                total_cost += val.get('gpt_cost', 0.0)

            if cit.get('quote_verification'):
                # Quote verification is deterministic, no cost
                pass

            if cit.get('support_check'):
                sup = cit['support_check'].get('analysis', {})
                total_tokens += sup.get('gpt_tokens', 0)
                total_cost += sup.get('gpt_cost', 0.0)

        return {
            "total_tokens": total_tokens,
            "total_cost": f"${total_cost:.4f}",
            "avg_cost_per_citation": f"${(total_cost / len(citations)):.4f}" if citations else "$0.00"
        }

    def add_to_review_queue(self, citation_num: int, footnote_num: int,
                           issue: str, severity: str, details: str):
        """Add citation to human review queue."""
        self.human_review_queue.append({
            "citation_num": citation_num,
            "footnote_num": footnote_num,
            "issue": issue,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def save_report(self, report: Dict, filename: str = None) -> Path:
        """Save report to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"r1_validation_report_{timestamp}.json"

        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved validation report to {output_path}")
        return output_path

    def generate_html_report(self, report: Dict, filename: str = None) -> Path:
        """Generate HTML report for human review."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"r1_validation_report_{timestamp}.html"

        output_path = self.output_dir / filename

        html = self._build_html_report(report)

        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"Saved HTML report to {output_path}")
        return output_path

    def _build_html_report(self, report: Dict) -> str:
        """Build HTML report content."""
        summary = report['validation_summary']
        queue = report.get('human_review_queue', [])
        costs = report.get('cost_analysis', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>R1 Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #8C1515; }}
        h2 {{ color: #2E2D29; border-bottom: 2px solid #8C1515; padding-bottom: 5px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .stat-label {{ font-weight: bold; }}
        .stat-value {{ color: #8C1515; font-size: 1.2em; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #8C1515; color: white; }}
        .error {{ background-color: #ffebee; }}
        .warning {{ background-color: #fff3e0; }}
        .success {{ background-color: #e8f5e9; }}
    </style>
</head>
<body>
    <h1>R1 Cite Checking Validation Report</h1>
    <p>Generated: {report['report_metadata']['generated_at']}</p>

    <h2>Summary Statistics</h2>
    <div class="summary">
        <div class="stat">
            <div class="stat-label">Total Citations:</div>
            <div class="stat-value">{summary['total_citations']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Validated:</div>
            <div class="stat-value">{summary['citations_validated']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Correct:</div>
            <div class="stat-value">{summary['citations_correct']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">With Errors:</div>
            <div class="stat-value">{summary['citations_with_errors']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Accuracy:</div>
            <div class="stat-value">{summary['accuracy_rate']}</div>
        </div>
    </div>

    <h2>Quote Verification</h2>
    <div class="summary">
        <div class="stat">
            <div class="stat-label">Quotes Checked:</div>
            <div class="stat-value">{summary['quotes_checked']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Accurate:</div>
            <div class="stat-value">{summary['quotes_accurate']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Accuracy:</div>
            <div class="stat-value">{summary['quote_accuracy_rate']}</div>
        </div>
    </div>

    <h2>Cost Analysis</h2>
    <div class="summary">
        <div class="stat">
            <div class="stat-label">Total Tokens:</div>
            <div class="stat-value">{costs.get('total_tokens', 0):,}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Total Cost:</div>
            <div class="stat-value">{costs.get('total_cost', '$0.00')}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Avg per Citation:</div>
            <div class="stat-value">{costs.get('avg_cost_per_citation', '$0.00')}</div>
        </div>
    </div>

    <h2>Human Review Queue ({len(queue)} items)</h2>
    <table>
        <tr>
            <th>Citation #</th>
            <th>Footnote #</th>
            <th>Issue</th>
            <th>Severity</th>
            <th>Details</th>
        </tr>
"""

        for item in queue:
            severity_class = {
                'critical': 'error',
                'major': 'warning',
                'minor': 'success'
            }.get(item.get('severity', '').lower(), '')

            html += f"""
        <tr class="{severity_class}">
            <td>{item.get('citation_num', 'N/A')}</td>
            <td>{item.get('footnote_num', 'N/A')}</td>
            <td>{item.get('issue', '')}</td>
            <td>{item.get('severity', '')}</td>
            <td>{item.get('details', '')}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""

        return html
