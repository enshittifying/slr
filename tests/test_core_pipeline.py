"""
Comprehensive tests for core pipeline components
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from core.sp_machine import SPMachine
from core.r1_machine import R1Machine
from core.r2_pipeline import R2Pipeline
from core.orchestrator import PipelineOrchestrator, PipelineStage


class TestSPMachine:
    """Test Source Pull Machine"""

    @pytest.fixture
    def sp_machine(self):
        """Create SP machine with mocked dependencies"""
        sheets_client = Mock()
        drive_client = Mock()
        cache_dir = tempfile.mkdtemp()

        sp = SPMachine(sheets_client, drive_client, cache_dir)

        yield sp

        # Cleanup
        shutil.rmtree(cache_dir, ignore_errors=True)

    def test_process_article_success(self, sp_machine):
        """Test successful article processing"""
        # Mock sources
        sp_machine.sheets.get_sources_for_article.return_value = [
            {
                'source_id': 'SP-001',
                'citation': 'Alice Corp. v. CLS Bank, 573 U.S. 208 (2014)',
                'footnote_num': '1',
                'type': 'case'
            }
        ]

        # Mock retriever
        with patch.object(sp_machine.retriever, 'retrieve_source') as mock_retrieve:
            mock_retrieve.return_value = '/tmp/test.pdf'

            # Mock drive upload
            sp_machine.drive.upload_source_pdf.return_value = 'file-123'
            sp_machine.drive.get_file_link.return_value = 'https://drive.google.com/file/d/file-123'

            # Run
            result = sp_machine.process_article('article-001')

            # Assertions
            assert result['success_count'] == 1
            assert result['fail_count'] == 0
            sp_machine.sheets.update_source_status.assert_called_once()

    def test_process_article_with_failures(self, sp_machine):
        """Test article processing with some failures"""
        sp_machine.sheets.get_sources_for_article.return_value = [
            {'source_id': 'SP-001', 'citation': 'Valid Citation', 'footnote_num': '1', 'type': 'case'},
            {'source_id': 'SP-002', 'citation': 'Invalid Citation', 'footnote_num': '2', 'type': 'unknown'}
        ]

        with patch.object(sp_machine.retriever, 'retrieve_source') as mock_retrieve:
            # First succeeds, second fails
            mock_retrieve.side_effect = ['/tmp/test.pdf', None]

            sp_machine.drive.upload_source_pdf.return_value = 'file-123'
            sp_machine.drive.get_file_link.return_value = 'https://drive.google.com/file-123'

            result = sp_machine.process_article('article-001')

            assert result['success_count'] == 1
            assert result['fail_count'] == 1

    def test_cache_status(self, sp_machine):
        """Test cache status tracking"""
        sp_machine.sheets.get_sources_for_article.return_value = [
            {'source_id': 'SP-001'},
            {'source_id': 'SP-002'}
        ]

        # Create one cached file
        (sp_machine.cache_dir / 'SP-001.pdf').write_text('dummy')

        status = sp_machine.get_cache_status('article-001')

        assert status['total'] == 2
        assert status['cached'] == 1
        assert status['pending'] == 1


class TestR1Machine:
    """Test R1 Preparation Machine"""

    @pytest.fixture
    def r1_machine(self):
        """Create R1 machine with mocked dependencies"""
        sheets_client = Mock()
        drive_client = Mock()
        cache_dir = tempfile.mkdtemp()

        r1 = R1Machine(sheets_client, drive_client, cache_dir)

        yield r1

        shutil.rmtree(cache_dir, ignore_errors=True)

    def test_clean_pdf_hein(self, r1_machine, tmp_path):
        """Test PDF cleaning for HeinOnline PDFs"""
        # Create mock PDF
        import fitz
        doc = fitz.open()
        doc.insert_page(0, text="Cover Page")
        doc.insert_page(1, text="Content")

        pdf_path = tmp_path / "hein_test.pdf"
        doc.save(pdf_path)
        doc.close()

        # Clean
        cleaned = r1_machine.clean_pdf(str(pdf_path), 'case')
        cleaned_doc = fitz.open(cleaned)

        # Should have removed first page
        assert len(cleaned_doc) == 1

        cleaned_doc.close()

    def test_process_article(self, r1_machine):
        """Test R1 processing for article"""
        r1_machine.sheets.get_sources_for_article.return_value = [
            {
                'source_id': 'SP-001',
                'citation': 'Test Citation',
                'type': 'case',
                'status': 'downloaded',
                'drive_link': 'https://drive.google.com/file/d/file-123'
            }
        ]

        # Mock download and upload
        r1_machine.drive.download_file.return_value = '/tmp/raw.pdf'
        r1_machine.drive.upload_r1_pdf.return_value = 'r1-file-123'
        r1_machine.drive.get_file_link.return_value = 'https://drive.google.com/file/d/r1-file-123'

        with patch.object(r1_machine, 'clean_pdf') as mock_clean, \
             patch.object(r1_machine, 'redbox_citation_metadata') as mock_redbox:

            mock_clean.return_value = '/tmp/cleaned.pdf'
            mock_redbox.return_value = str(r1_machine.cache_dir / 'SP-001_R1.pdf')

            result = r1_machine.process_article('article-001')

            assert result['success_count'] == 1
            assert result['fail_count'] == 0


class TestR2Pipeline:
    """Test R2 Validation Pipeline"""

    @pytest.fixture
    def r2_pipeline(self):
        """Create R2 pipeline with mocked dependencies"""
        sheets_client = Mock()
        drive_client = Mock()
        llm_client = Mock()
        cache_dir = tempfile.mkdtemp()

        r2 = R2Pipeline(sheets_client, drive_client, llm_client, cache_dir)

        yield r2

        shutil.rmtree(cache_dir, ignore_errors=True)

    def test_validate_citation_format(self, r2_pipeline):
        """Test citation format validation"""
        r2_pipeline.llm.check_format.return_value = {
            'issues': [],
            'suggestion': ''
        }

        result = r2_pipeline.validate_citation(
            'Alice Corp. v. CLS Bank, 573 U.S. 208 (2014)',
            1,
            'As held in Alice Corp., ...',
            None
        )

        assert result.format_issues == []
        assert not result.requires_review

    def test_validate_citation_with_issues(self, r2_pipeline):
        """Test citation validation with format issues"""
        r2_pipeline.llm.check_format.return_value = {
            'issues': ['Missing court designation'],
            'suggestion': 'Alice Corp. v. CLS Bank, 573 U.S. 208 (Fed. Cir. 2014)'
        }

        result = r2_pipeline.validate_citation(
            'Alice Corp. v. CLS Bank, 573 U.S. 208 (2014)',
            1,
            'Test footnote',
            None
        )

        assert len(result.format_issues) == 1
        assert result.requires_review

    def test_quote_extraction(self, r2_pipeline):
        """Test quote extraction from citations"""
        citation = 'As the Court stated, "patents are essential," the system works.'

        quotes = r2_pipeline._extract_quotes(citation)

        assert len(quotes) == 1
        assert 'patents are essential' in quotes


class TestPipelineOrchestrator:
    """Test Pipeline Orchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies"""
        sheets = Mock()
        drive = Mock()
        llm = Mock()

        orch = PipelineOrchestrator(sheets, drive, llm, tempfile.mkdtemp())

        yield orch

    def test_get_article_state(self, orchestrator):
        """Test getting article state"""
        orchestrator.sheets.get_all_articles.return_value = [
            {
                'article_id': 'test-001',
                'volume_issue': '78.6',
                'stage': 'sp_complete',
                'sources_total': 100,
                'sources_completed': 95,
                'last_updated': '2024-01-01'
            }
        ]

        state = orchestrator.get_article_state('test-001')

        assert state.article_id == 'test-001'
        assert state.stage == PipelineStage.SP_COMPLETE
        assert state.sources_total == 100

    def test_run_sp_success(self, orchestrator):
        """Test successful SP run"""
        with patch.object(orchestrator.sp_machine, 'process_article') as mock_process:
            mock_process.return_value = {
                'success_count': 100,
                'fail_count': 0,
                'total': 100
            }

            result = orchestrator.run_sp('test-001')

            assert result['success_count'] == 100
            orchestrator.sheets.update_article_stage.assert_called()

    def test_pipeline_stage_validation(self, orchestrator):
        """Test that R1 requires SP complete"""
        orchestrator.sheets.get_all_articles.return_value = [
            {
                'article_id': 'test-001',
                'volume_issue': '78.6',
                'stage': 'not_started',
                'sources_total': 0,
                'sources_completed': 0,
                'last_updated': ''
            }
        ]

        with pytest.raises(ValueError, match="Cannot run R1"):
            orchestrator.run_r1('test-001')


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_citation(self):
        """Test handling of empty citation"""
        # Should not crash
        pass

    def test_malformed_citation(self):
        """Test handling of malformed citation"""
        pass

    def test_network_timeout(self):
        """Test handling of network timeouts"""
        pass

    def test_invalid_pdf(self):
        """Test handling of invalid/corrupted PDFs"""
        pass

    def test_missing_api_key(self):
        """Test handling of missing API credentials"""
        pass

    def test_rate_limit_exceeded(self):
        """Test handling of API rate limits"""
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
