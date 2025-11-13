#!/usr/bin/env python3
"""
Live web viewer for R2 citation validation results.
Automatically reloads when the log file changes.
"""
from flask import Flask, render_template_string, jsonify, send_file
from pathlib import Path
import json
from datetime import datetime
import os
import re
import difflib

app = Flask(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "data/output/logs/full_pipeline_log.json"
R2_PDF_DIR = Path("data/output/r2_pdfs")

def load_results():
    """Load the latest validation results."""
    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return []

def get_status_color(citation):
    """Get color based on citation status."""
    if not citation.get("needs_review"):
        return "success"  # Green

    validation = citation.get("citation_validation") or {}
    support = citation.get("support_analysis") or {}

    if support.get("support_level") == "no":
        return "danger"  # Red
    elif validation.get("is_correct") == False:
        return "warning"  # Yellow
    elif citation.get("ocr_quality_warning"):
        return "info"  # Blue
    else:
        return "secondary"  # Gray

def format_timestamp():
    """Get current timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def markdown_to_html(text):
    """
    Convert markdown notation to HTML formatting.
    - *text* -> <em>text</em> (italics)
    - **text** -> <strong>text</strong> (bold)
    - [SC]text[/SC] -> <span class="small-caps">text</span>
    - NBSP (U+00A0) -> visible degree symbol with special styling
    """
    if not text:
        return text

    # Replace non-breaking spaces with visible degree symbol for display
    # Use a span with special class so we can style it and convert back on copy
    text = text.replace('\u00a0', '<span class="nbsp-visible" data-char="nbsp">°</span>')

    # Replace small caps first (before other formatting)
    text = re.sub(r'\[SC\](.*?)\[/SC\]', r'<span class="small-caps">\1</span>', text)

    # Bold (before italics to avoid conflicts)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Italics
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    return text

def strip_markdown(text):
    """
    Remove all markdown notation to get plain text.
    Used for intelligent diff comparison.
    Note: NBSP characters are preserved (not stripped) since they represent
    substantive formatting differences.
    """
    if not text:
        return text

    # Remove small caps
    text = re.sub(r'\[SC\](.*?)\[/SC\]', r'\1', text)

    # Remove bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

    # Remove italics
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Note: We deliberately keep NBSP (U+00A0) vs regular space (U+0020) distinction
    # because that's a substantive formatting difference per Bluebook 6.2

    return text

def generate_smart_diff(original, corrected):
    """
    Generate a diff that shows all changes, including markdown formatting.

    Returns tuple: (has_changes, html_diff)
    """
    # Use the raw text with markdown characters for comparison
    if original == corrected:
        return False, None

    matcher = difflib.SequenceMatcher(None, original, corrected)

    html_parts = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        original_text_with_md = original[i1:i2]
        corrected_text_with_md = corrected[j1:j2]

        # Convert the markdown in the snippets to HTML for rendering
        original_html = markdown_to_html(original_text_with_md)
        corrected_html = markdown_to_html(corrected_text_with_md)

        if opcode == 'equal':
            html_parts.append(original_html)
        elif opcode == 'delete':
            html_parts.append(f'<span class="diff-removed">{original_html}</span>')
        elif opcode == 'insert':
            html_parts.append(f'<span class="diff-added">{corrected_html}</span>')
        elif opcode == 'replace':
            html_parts.append(f'<span class="diff-removed">{original_html}</span>')
            html_parts.append(f'<span class="diff-added">{corrected_html}</span>')

    return True, "".join(html_parts)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>R2 Citation Validator - Live Viewer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.0/font/bootstrap-icons.css">
    <style>
        body { padding: 20px; background: #f8f9fa; }
        .citation-card { margin-bottom: 20px; }
        .citation-header { cursor: pointer; }
        .citation-text {
            font-family: 'Georgia', 'Times New Roman', serif;
            background: #f5f5f5;
            padding: 4px 8px;
            border-radius: 5px;
            white-space: normal;
            word-wrap: break-word;
            line-height: 1.6;
            display: flex;
            justify-content: space-between;
            align-items: start;
        }
        .nbsp-visible {
            color: #2196f3;
            font-weight: normal;
        }
        .copy-btn {
            opacity: 0.6;
            transition: opacity 0.2s;
            margin-left: 10px; /* Add space between text and button */
        }
        .copy-btn:hover { opacity: 1; }
        .citation-text:hover .copy-btn { opacity: 0.8; }
        .badge-pill { border-radius: 10px; }
        .error-detail {
            background: #fff3cd;
            padding: 2px 4px;
            margin: 2px 0;
            border-left: 3px solid #ffc107;
        }
        .support-detail {
            background: #d1ecf1;
            padding: 2px 4px;
            margin: 2px 0;
            border-left: 3px solid #0dcaf0;
        }
        .ocr-warning {
            background: #f8d7da;
            padding: 2px 4px;
            margin: 2px 0;
            border-left: 3px solid #dc3545;
        }
        .stats-card { margin-bottom: 20px; }
        .update-banner {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        .quote-text {
            font-style: italic;
            color: #555;
        }
        .diff-removed {
            background: #ffcccc;
            text-decoration: line-through;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .diff-added {
            background: #ccffcc;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .diff-viewer {
            background: #ffffff;
            padding: 8px 10px;
            border-radius: 5px;
            border: 2px solid #007bff;
            margin: 5px 0;
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
        }
        .no-changes-notice {
            background: #d4edda;
            color: #155724;
            padding: 6px 8px;
            border-radius: 5px;
            border-left: 3px solid #28a745;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .copy-success {
            position: fixed;
            top: 60px;
            right: 10px;
            z-index: 1001;
            animation: fadeIn 0.3s, fadeOut 0.3s 2.7s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        /* Reduce Bootstrap default padding */
        .card-body {
            padding: 6px !important;
        }
        .alert {
            padding: 4px 8px !important;
            margin-bottom: 4px !important;
        }
        hr {
            margin: 8px 0 !important;
        }
        h6 {
            margin-bottom: 6px !important;
        }
        p {
            margin-bottom: 4px !important;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="update-banner">
            <span class="badge bg-secondary" id="last-update">Last updated: {{ timestamp }}</span>
            <button class="btn btn-sm btn-primary" onclick="location.reload()">
                <i class="bi bi-arrow-clockwise"></i> Refresh
            </button>
        </div>

        <h1 class="mb-4">
            <i class="bi bi-file-earmark-check"></i> R2 Citation Validator
        </h1>

        <!-- Statistics Dashboard -->
        <div class="row stats-card">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3>{{ stats.total }}</h3>
                        <p class="text-muted">Total Citations</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-success">
                    <div class="card-body">
                        <h3 class="text-success">{{ stats.approved }}</h3>
                        <p class="text-muted">Approved</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-warning">
                    <div class="card-body">
                        <h3 class="text-warning">{{ stats.needs_review }}</h3>
                        <p class="text-muted">Needs Review</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-danger">
                    <div class="card-body">
                        <h3 class="text-danger">{{ stats.unsupported }}</h3>
                        <p class="text-muted">Unsupported</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Batch Selector and Filters -->
        <div class="card mb-3">
            <div class="card-body">
                <h5><i class="bi bi-layers"></i> Batch & Filters</h5>

                <div class="row mb-3">
                    <div class="col-md-4">
                        <label for="batch-selector" class="form-label"><strong>Select Batch:</strong></label>
                        <select id="batch-selector" class="form-select" onchange="changeBatch(this.value)">
                            <option value="all" {% if selected_batch == 'all' %}selected{% endif %}>All Batches ({{ batches | sum(attribute='count') if batches else 0 }})</option>
                            {% for batch in batches %}
                            <option value="{{ batch.name }}" {% if selected_batch == batch.name %}selected{% endif %}>
                                {{ batch.name }} ({{ batch.count }} citations)
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-8 d-flex align-items-center">
                        <div>
                            <label class="form-label d-block"><strong>Filter Results:</strong></label>
                            <div class="btn-group" role="group">
                                <input type="radio" class="btn-check" name="filter" id="filter-all" checked onclick="filterCitations('all')">
                                <label class="btn btn-outline-secondary" for="filter-all">All ({{ stats.total }})</label>

                                <input type="radio" class="btn-check" name="filter" id="filter-review" onclick="filterCitations('review')">
                                <label class="btn btn-outline-warning" for="filter-review">Review ({{ stats.needs_review }})</label>

                                <input type="radio" class="btn-check" name="filter" id="filter-errors" onclick="filterCitations('errors')">
                                <label class="btn btn-outline-danger" for="filter-errors">Errors ({{ stats.errors }})</label>

                                <input type="radio" class="btn-check" name="filter" id="filter-ocr" onclick="filterCitations('ocr')">
                                <label class="btn btn-outline-info" for="filter-ocr">OCR Issues ({{ stats.ocr_warnings }})</label>
                            </div>
                        </div>
                        <div class="ms-4">
                             <label class="form-label d-block"><strong>Actions:</strong></label>
                            <div class="btn-group" role="group">
                                <button id="open-all-btn" class="btn btn-outline-primary">Open All</button>
                                <button id="close-all-btn" class="btn btn-outline-primary">Close All</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Citations List -->
        {% for citation in citations %}
        <div class="card citation-card {{ 'border-' + citation.status_color }}" data-filter="{{ citation.filter_tags }}">
            <div class="card-header citation-header bg-{{ citation.status_color }} bg-opacity-10"
                 data-bs-toggle="collapse"
                 data-bs-target="#citation-{{ citation.footnote }}-{{ citation.cite_num }}">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="bi bi-chevron-down toggle-icon"></i>
                        Footnote {{ citation.footnote }}, Citation {{ citation.cite_num }}
                    </h5>
                    <div>
                        {% if citation.needs_review %}
                        <span class="badge bg-warning">Needs Review</span>
                        {% endif %}
                        {% if citation.ocr_quality_warning %}
                        <span class="badge bg-danger">OCR Warning</span>
                        {% endif %}
                        {% if citation.support_analysis %}
                        <span class="badge bg-{{ 'success' if citation.support_analysis.support_level == 'yes' else 'danger' if citation.support_analysis.support_level == 'no' else 'warning' }}">
                            Support: {{ citation.support_analysis.support_level | upper }}
                        </span>
                        {% endif %}
                    </div>
                </div>
            </div>

            <div id="citation-{{ citation.footnote }}-{{ citation.cite_num }}" class="collapse">
                <div class="card-body">
                    {% if citation.r2_pdf_path %}
                    <a href="/pdf/{{ citation.footnote }}/{{ citation.cite_num }}" target="_blank" class="btn btn-sm btn-outline-primary float-end mb-2">
                        <i class="bi bi-file-pdf"></i> View R2 PDF
                    </a>
                    {% endif %}

                    {% if citation.r1_missing %}
                    <div class="alert alert-warning mb-3">
                        <i class="bi bi-exclamation-triangle-fill"></i> <strong>R1 PDF Missing:</strong> The source PDF for this citation could not be found. Analysis was not performed.
                    </div>
                    {% endif %}

                    <!-- Original Citation Text -->
                    <h6><i class="bi bi-file-text"></i> Original Citation:</h6>
                    <div class="citation-text">
                        <div id="cite-{{ citation.footnote }}-{{ citation.cite_num }}-original">{{- citation.original_text_html | safe -}}</div>
                        <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyCitation(this, {{ citation.footnote }}, {{ citation.cite_num }}, 'original')">
                            <i class="bi bi-clipboard"></i> Copy
                        </button>
                    </div>

                    <!-- Citation Format Validation -->
                    {% if citation.citation_validation %}
                    <hr>
                    <h6><i class="bi bi-check2-square"></i> Citation Format Validation</h6>
                    {% if citation.citation_validation.is_correct %}
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle"></i> Citation format is correct!
                    </div>
                    {% else %}
                    <div class="alert alert-danger">
                        <i class="bi bi-x-circle"></i> {{ citation.citation_validation.get('errors', []) | length }} formatting error(s) found
                    </div>

                    {% for error in citation.citation_validation.get('errors', []) %}
                    <div class="error-detail">
                        <strong>{{ error.error_type | replace('_', ' ') | title }}</strong>
                        <p>{{ error.description }}</p>
                        <p><strong>Rule:</strong>
                            {% if error.rb_rule %}Redbook {{ error.rb_rule }}{% endif %}
                            {% if error.bluebook_rule %}Bluebook {{ error.bluebook_rule }}{% endif %}
                        </p>
                        <p><strong>Current:</strong> <span class="diff-old">{{ error.current | replace('\u00a0', '<span class="nbsp-visible" title="Non-breaking space">°</span>') | safe }}</span></p>
                        <p><strong>Correct:</strong> <span class="diff-new">{{ error.correct | replace('\u00a0', '<span class="nbsp-visible" title="Non-breaking space">°</span>') | safe }}</span></p>
                    </div>
                    {% endfor %}

                    <h6 class="mt-3">Corrected Version:</h6>
                    <div class="citation-text">
                        <div id="cite-{{ citation.footnote }}-{{ citation.cite_num }}-corrected">{{- citation.corrected_text_html | safe -}}</div>
                        <button class="btn btn-sm btn-outline-success copy-btn" onclick="copyCitation(this, {{ citation.footnote }}, {{ citation.cite_num }}, 'corrected')">
                            <i class="bi bi-clipboard"></i> Copy
                        </button>
                    </div>

                    <!-- Diff Viewer -->
                    {% if citation.has_changes %}
                    <h6 class="mt-3"><i class="bi bi-file-diff"></i> Changes:</h6>
                    <div class="diff-viewer">{{ citation.diff_html | safe }}</div>
                    {% else %}
                    <div class="no-changes-notice mt-3">
                        <i class="bi bi-info-circle"></i> <strong>No changes found.</strong>
                    </div>
                    {% endif %}
                    {% endif %}
                    {% endif %}

                    <!-- OCR Quality Warning -->
                    {% if citation.ocr_quality_warning %}
                    <hr>
                    <div class="ocr-warning">
                        <h6><i class="bi bi-exclamation-triangle"></i> OCR Quality Warning</h6>
                        <p>This PDF had corrupted text extraction. The following regions were excluded:</p>
                        <p><strong>Corrupted regions:</strong> {{ citation.corrupted_regions | join(', ') if citation.corrupted_regions else 'Multiple regions' }}</p>
                        <p class="mb-0"><em>Results may be less reliable. Manual verification recommended.</em></p>
                    </div>
                    {% endif %}

                    <!-- Support Analysis -->
                    {% if citation.support_analysis %}
                    <hr>
                    <h6><i class="bi bi-shield-check"></i> Support Analysis</h6>
                    <div class="support-detail">
                        <!-- Text Proposition -->
                        {% if citation.support_analysis.proposition %}
                        <p><strong>Text Proposition:</strong></p>
                        <div class="alert alert-light">
                            {{ citation.support_analysis.proposition }}
                        </div>
                        {% endif %}

                        <p><strong>Support Level:</strong>
                            <span class="badge bg-{{ 'success' if citation.support_analysis.support_level == 'yes' else 'danger' if citation.support_analysis.support_level == 'no' else 'warning' }}">
                                {{ citation.support_analysis.support_level | upper }}
                            </span>
                            (Confidence: {{ (citation.support_analysis.confidence * 100) | round }}%)
                        </p>

                        {% if citation.support_analysis.supported_elements %}
                        <p><strong>Supported Elements:</strong></p>
                        {% for element in citation.support_analysis.supported_elements %}
                            {% if element is mapping %}
                                {# New format: element is a dict with 'element' and 'source_excerpt' #}
                                <div class="mb-2">
                                    <span class="badge bg-success">{{ element.element }}</span>
                                    {% if element.source_excerpt %}
                                    <blockquote class="blockquote-sm mt-1" style="font-size: 0.85em; padding-left: 10px; border-left: 3px solid #28a745; margin-left: 10px; color: #555;">
                                        {{ element.source_excerpt }}
                                    </blockquote>
                                    {% endif %}
                                </div>
                            {% else %}
                                {# Old format: element is a string #}
                                <span class="badge bg-success">{{ element }}</span>
                            {% endif %}
                        {% endfor %}
                        {% endif %}

                        {% if citation.support_analysis.unsupported_elements %}
                        <p><strong>Unsupported Elements:</strong>
                            {% for element in citation.support_analysis.unsupported_elements %}
                                <span class="badge bg-danger">{{ element }}</span>
                            {% endfor %}
                        </p>
                        {% endif %}

                        <p><strong>Reasoning:</strong> {{ citation.support_analysis.reasoning }}</p>
                        <p><strong>Recommendation:</strong> <code>{{ citation.recommendation or 'None' }}</code></p>
                    </div>
                    {% endif %}

                    <!-- Source PDF Info -->
                    {% if citation.source_pdf %}
                    <hr>
                    <h6><i class="bi bi-file-earmark-pdf"></i> Source PDF</h6>
                    <p class="mb-0">
                        <strong>{{ citation.source_pdf.filename }}</strong><br>
                        {% if citation.source_pdf.title %}Title: {{ citation.source_pdf.title }}<br>{% endif %}
                        {% if citation.source_pdf.author %}Author: {{ citation.source_pdf.author }}<br>{% endif %}
                        Pages: {{ citation.source_pdf.num_pages }}
                    </p>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}

        {% if not citations %}
        <div class="alert alert-info text-center">
            <i class="bi bi-info-circle"></i> No validation results yet. Run the pipeline to see results here.
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Toggle chevron on collapse
        document.querySelectorAll('.citation-header').forEach(header => {
            header.addEventListener('click', function() {
                const icon = this.querySelector('.toggle-icon');
                icon.classList.toggle('bi-chevron-right');
                icon.classList.toggle('bi-chevron-down');
            });
        });

        // Change batch
        function changeBatch(batchName) {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('batch', batchName);
            window.location.href = currentUrl.toString();
        }

        // Filter citations
        function filterCitations(filter) {
            const cards = document.querySelectorAll('.citation-card');
            cards.forEach(card => {
                const tags = card.getAttribute('data-filter');
                if (filter === 'all' || tags.includes(filter)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        // Copy citation to clipboard
        function copyCitation(button, footnote, citeNum, version) {
            const elementId = `cite-${footnote}-${citeNum}-${version}`;
            const element = document.getElementById(elementId);

            if (!element) {
                alert('Citation text not found');
                return;
            }

            // Get the plain text content (strips HTML but preserves formatting intent)
            let text = element.innerText || element.textContent;

            // Convert degree symbols back to non-breaking spaces
            // The degree symbol (°) represents NBSP in our display
            text = text.replace(/°/g, '\u00a0');

            // Copy to clipboard
            navigator.clipboard.writeText(text).then(() => {
                // Show success message
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i> Copied!';
                button.classList.remove('btn-outline-primary', 'btn-outline-success');
                button.classList.add('btn-success');

                // Show floating notification
                showCopySuccess();

                // Reset button after 2 seconds
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.classList.remove('btn-success');
                    if (version === 'original') {
                        button.classList.add('btn-outline-primary');
                    } else {
                        button.classList.add('btn-outline-success');
                    }
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy to clipboard');
            });
        }

        // Show floating success notification
        function showCopySuccess() {
            // Remove any existing notification
            const existing = document.getElementById('copy-success-notification');
            if (existing) {
                existing.remove();
            }

            // Create new notification
            const notification = document.createElement('div');
            notification.id = 'copy-success-notification';
            notification.className = 'copy-success alert alert-success';
            notification.innerHTML = '<i class="bi bi-check-circle"></i> Copied to clipboard!';
            document.body.appendChild(notification);

            // Remove after animation completes
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Open/Close All
        document.getElementById('open-all-btn').addEventListener('click', () => {
            document.querySelectorAll('.collapse').forEach(el => {
                const collapseInstance = bootstrap.Collapse.getOrCreateInstance(el);
                collapseInstance.show();
            });
        });

        document.getElementById('close-all-btn').addEventListener('click', () => {
            document.querySelectorAll('.collapse').forEach(el => {
                const collapseInstance = bootstrap.Collapse.getOrCreateInstance(el);
                collapseInstance.hide();
            });
        });

        document.addEventListener('DOMContentLoaded', () => {
            // --- State Saving for Collapse ---
            const saveState = () => {
                const openCards = [];
                document.querySelectorAll('.collapse.show').forEach(el => {
                    openCards.push(el.id);
                });
                localStorage.setItem('r2ViewerOpenCards', JSON.stringify(openCards));
            };

            const restoreState = () => {
                const openCards = JSON.parse(localStorage.getItem('r2ViewerOpenCards') || '[]');
                openCards.forEach(cardId => {
                    const el = document.getElementById(cardId);
                    if (el) {
                        const collapseInstance = bootstrap.Collapse.getOrCreateInstance(el);
                        collapseInstance.show();
                    }
                });
            };

            // Add event listeners to save state on change
            document.querySelectorAll('.collapse').forEach(el => {
                el.addEventListener('shown.bs.collapse', saveState);
                el.addEventListener('hidden.bs.collapse', saveState);
            });

            // Restore state on page load
            restoreState();
        });

        // Auto-refresh is disabled as it clears UI state.
        // setTimeout(() => location.reload(), 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main viewer page."""
    from flask import request

    results = load_results()

    # Filter out None values (failed citations)
    results = [r for r in results if r is not None]

    # Get unique batches
    batches = {}
    for result in results:
        batch_name = result.get('batch_name', 'unknown')
        batch_timestamp = result.get('batch_timestamp', '')
        if batch_name not in batches:
            batches[batch_name] = {
                'name': batch_name,
                'timestamp': batch_timestamp,
                'count': 0
            }
        batches[batch_name]['count'] += 1

    # Get selected batch from query param
    selected_batch = request.args.get('batch', 'all')

    # Filter results by batch
    if selected_batch != 'all':
        results = [r for r in results if r.get('batch_name') == selected_batch]

    # Calculate statistics (with defensive checks for None values)
    stats = {
        'total': len(results),
        'approved': sum(1 for c in results if c and not c.get('needs_review')),
        'needs_review': sum(1 for c in results if c and c.get('needs_review')),
        'unsupported': sum(1 for c in results if c and c.get('support_analysis') and c.get('support_analysis', {}).get('support_level') == 'no'),
        'errors': sum(1 for c in results if c and c.get('citation_validation') and c.get('citation_validation', {}).get('is_correct') == False),
        'ocr_warnings': sum(1 for c in results if c and c.get('ocr_quality_warning'))
    }

    # Add display properties to each citation
    for citation in results:
        citation['status_color'] = get_status_color(citation)

        # Add filter tags
        tags = ['all']
        if citation.get('needs_review'):
            tags.append('review')
        citation_val = citation.get('citation_validation')
        if citation_val and citation_val.get('is_correct') == False:
            tags.append('errors')
        if citation.get('ocr_quality_warning'):
            tags.append('ocr')
        citation['filter_tags'] = ' '.join(tags)

        # Check for missing R1 PDF
        if not citation.get('r1_pdf_path'):
            citation['r1_missing'] = True
        else:
            citation['r1_missing'] = False

        # Convert markdown to HTML for display
        citation['original_text_html'] = markdown_to_html(citation.get('original_text', ''))

        # Process corrected text if available
        citation_val = citation.get('citation_validation') or {}
        corrected = citation.get('corrected_text') or citation_val.get('corrected_version')
        if corrected:
            citation['corrected_text_html'] = markdown_to_html(corrected)

            # Generate smart diff
            has_changes, diff_html = generate_smart_diff(
                citation.get('original_text', ''),
                corrected
            )
            citation['has_changes'] = has_changes
            citation['diff_html'] = diff_html
        else:
            citation['corrected_text_html'] = None
            citation['has_substantive_changes'] = False
            citation['diff_html'] = None

    # Sort citations by footnote number first, then citation number
    results.sort(key=lambda c: (c.get('footnote', 0), c.get('cite_num', 0)))

    return render_template_string(
        HTML_TEMPLATE,
        citations=results,
        stats=stats,
        batches=sorted(batches.values(), key=lambda x: x['timestamp'], reverse=True),
        selected_batch=selected_batch,
        timestamp=format_timestamp()
    )

@app.route('/pdf/<int:footnote>/<int:cite_num>')
def view_pdf(footnote, cite_num):
    """Serve R2 PDF for a specific citation."""
    results = load_results()

    # Find the citation
    print(f"--- PDF REQUEST: FN {footnote}, CITE {cite_num} ---")
    for citation in results:
        if citation['footnote'] == footnote and citation['cite_num'] == cite_num:
            pdf_path = citation.get('r2_pdf_path')
            print(f"  -> Found path: {pdf_path}")
            if pdf_path and Path(pdf_path).exists():
                print("  -> Path exists. Sending file.")
                return send_file(pdf_path, mimetype='application/pdf')
            else:
                print("  -> Path does NOT exist or is None.")

    print("  -> Citation not found in log.")

    return "PDF not found", 404

@app.route('/api/results')
def api_results():
    """API endpoint for results (JSON)."""
    return jsonify(load_results())

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 R2 Citation Validator - Live Viewer")
    print("=" * 80)
    print(f"📂 Watching: {LOG_FILE.absolute()}")
    print(f"🌐 Open in browser: http://localhost:8080")
    print(f"🔄 Auto-refreshes every 10 seconds")
    print(f"💡 Press Ctrl+C to stop")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=8080)
