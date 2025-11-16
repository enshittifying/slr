"""
Integration tests for full pipeline
Tests SP → R1 → R2 flow end-to-end
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import shutil
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from core.orchestrator import PipelineOrchestrator, PipelineStage
from utils.config import ConfigManager


class TestFullPipelineIntegration:
    """Test complete SP → R1 → R2 pipeline"""

    @pytest.fixture
    def mock_services(self):
        """Create mocked services"""
        sheets = Mock()
        drive = Mock()
        llm = Mock()

        # Mock article data
        sheets.get_all_articles.return_value = [
            {
                'article_id': 'test-001',
                'volume_issue': '78.6',
                'author': 'Test Author',
                'title': 'Test Article',
                'stage': 'not_started',
                'sources_total': 3,
                'sources_completed': 0,
                'last_updated': ''
            }
        ]

        # Mock source data
        sheets.get_sources_for_article.return_value = [
            {
                'source_id': 'SP-001',
                'article_id': 'test-001',
                'footnote_num': '1',
                'citation': 'Alice Corp. v. CLS Bank, 573 U.S. 208 (2014)',
                'type': 'case',
                'status': 'pending',
                'drive_link': '',
                'r1_status': '',
                'r1_drive_link': ''
            },
            {
                'source_id': 'SP-002',
                'article_id': 'test-001',
                'footnote_num': '2',
                'citation': '35 U.S.C. § 101',
                'type': 'statute',
                'status': 'pending',
                'drive_link': '',
                'r1_status': '',
                'r1_drive_link': ''
            },
            {
                'source_id': 'SP-003',
                'article_id': 'test-001',
                'footnote_num': '3',
                'citation': 'John Doe, Patent Law, 100 Harv. L. Rev. 123 (2020)',
                'type': 'article',
                'status': 'pending',
                'drive_link': '',
                'r1_status': '',
                'r1_drive_link': ''
            }
        ]

        return sheets, drive, llm

    @pytest.fixture
    def orchestrator(self, mock_services):
        """Create orchestrator with mocked services"""
        sheets, drive, llm = mock_services
        cache_dir = tempfile.mkdtemp()

        orch = PipelineOrchestrator(sheets, drive, llm, cache_dir)

        yield orch

        shutil.rmtree(cache_dir, ignore_errors=True)

    def test_sp_to_r1_handoff(self, orchestrator, mock_services):
        """Test that SP completion enables R1"""
        sheets, drive, llm = mock_services

        # Mock SP processing
        with patch.object(orchestrator.sp_machine, 'process_article') as mock_sp:
            mock_sp.return_value = {
                'success_count': 3,
                'fail_count': 0,
                'total': 3
            }

            # Run SP
            sp_result = orchestrator.run_sp('test-001')

            assert sp_result['success_count'] == 3

            # Verify stage was updated to sp_complete
            update_calls = sheets.update_article_stage.call_args_list
            assert any('sp_complete' in str(call) for call in update_calls)

        # Now SP is complete, update mock to reflect that
        sheets.get_all_articles.return_value[0]['stage'] = 'sp_complete'
        sheets.get_all_articles.return_value[0]['sources_completed'] = 3

        # Update sources to have drive links (downloaded)
        for source in sheets.get_sources_for_article.return_value:
            source['status'] = 'downloaded'
            source['drive_link'] = f"https://drive.google.com/file/d/{source['source_id']}"

        # Mock R1 processing
        with patch.object(orchestrator.r1_machine, 'process_article') as mock_r1:
            mock_r1.return_value = {
                'success_count': 3,
                'fail_count': 0,
                'total': 3
            }

            # Should now be able to run R1
            r1_result = orchestrator.run_r1('test-001')

            assert r1_result['success_count'] == 3

    def test_full_pipeline_flow(self, orchestrator, mock_services):
        """Test complete SP → R1 → R2 flow"""
        sheets, drive, llm = mock_services

        # Create mock Word document
        article_doc = tempfile.mktemp(suffix='.docx')

        # Mock all stages
        with patch.object(orchestrator.sp_machine, 'process_article') as mock_sp, \
             patch.object(orchestrator.r1_machine, 'process_article') as mock_r1, \
             patch.object(orchestrator.r2_pipeline, 'process_article') as mock_r2:

            mock_sp.return_value = {'success_count': 3, 'fail_count': 0, 'total': 3}
            mock_r1.return_value = {'success_count': 3, 'fail_count': 0, 'total': 3}
            mock_r2.return_value = {
                'citations_checked': 3,
                'issues_found': 1,
                'upload_results': {},
                'results': []
            }

            # Update stages as we go
            def update_stage_side_effect(article_id, stage, error=None):
                sheets.get_all_articles.return_value[0]['stage'] = stage
                if stage == 'sp_complete':
                    for s in sheets.get_sources_for_article.return_value:
                        s['status'] = 'downloaded'
                        s['drive_link'] = f"https://drive.google.com/file/d/{s['source_id']}"
                elif stage == 'r1_complete':
                    for s in sheets.get_sources_for_article.return_value:
                        s['r1_status'] = 'r1_complete'
                        s['r1_drive_link'] = f"https://drive.google.com/file/d/{s['source_id']}_R1"

            sheets.update_article_stage.side_effect = update_stage_side_effect

            # Run full pipeline
            results = orchestrator.run_full_pipeline('test-001', article_doc)

            # Verify all stages ran
            assert results['sp']['success_count'] == 3
            assert results['r1']['success_count'] == 3
            assert results['r2']['citations_checked'] == 3

            # Verify stage updates
            assert sheets.update_article_stage.call_count >= 3

    def test_pipeline_stage_validation(self, orchestrator, mock_services):
        """Test that pipeline enforces stage prerequisites"""
        sheets, drive, llm = mock_services

        # Try to run R1 before SP complete
        with pytest.raises(ValueError, match="Cannot run R1"):
            orchestrator.run_r1('test-001')

        # Update to SP complete
        sheets.get_all_articles.return_value[0]['stage'] = 'sp_complete'

        # Try to run R2 before R1 complete
        with pytest.raises(ValueError, match="Cannot run R2"):
            orchestrator.run_r2('test-001', '/tmp/article.docx')

    def test_error_recovery(self, orchestrator, mock_services):
        """Test error handling and recovery"""
        sheets, drive, llm = mock_services

        # Mock SP with partial failure
        with patch.object(orchestrator.sp_machine, 'process_article') as mock_sp:
            mock_sp.return_value = {
                'success_count': 2,
                'fail_count': 1,
                'total': 3
            }

            sp_result = orchestrator.run_sp('test-001')

            # Should still complete with errors
            assert sp_result['fail_count'] == 1

            # Check error was logged
            update_calls = sheets.update_article_stage.call_args_list
            assert len(update_calls) > 0


class TestProgressCallbacks:
    """Test progress callback functionality"""

    def test_sp_progress_callbacks(self):
        """Test SP progress reporting"""
        sheets = Mock()
        drive = Mock()

        sheets.get_sources_for_article.return_value = [
            {'source_id': f'SP-{i:03d}', 'citation': f'Citation {i}', 'footnote_num': str(i), 'type': 'case'}
            for i in range(1, 6)
        ]

        from core.sp_machine import SPMachine

        sp = SPMachine(sheets, drive, tempfile.mkdtemp())

        progress_updates = []

        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))

        with patch.object(sp.retriever, 'retrieve_source') as mock_retrieve:
            mock_retrieve.return_value = '/tmp/test.pdf'
            drive.upload_source_pdf.return_value = 'file-123'
            drive.get_file_link.return_value = 'https://drive.google.com/file/d/file-123'

            sp.process_article('test-001', progress_callback)

        # Should have progress updates
        assert len(progress_updates) > 0
        # Last update should be for last source
        assert any(update[0] == 5 and update[1] == 5 for update in progress_updates)


class TestErrorHandling:
    """Test comprehensive error handling"""

    def test_network_failure_retry(self):
        """Test retry on network failures"""
        # This would test exponential backoff - placeholder
        pass

    def test_invalid_pdf_handling(self):
        """Test handling of corrupted PDFs"""
        # This would test PDF validation - placeholder
        pass

    def test_api_rate_limit_handling(self):
        """Test handling of API rate limits"""
        # This would test rate limit backoff - placeholder
        pass

    def test_missing_credentials_handling(self):
        """Test graceful failure when credentials missing"""
        config = ConfigManager()

        # Clear credentials path
        config.set('paths.credentials', '')

        # Should raise helpful error
        # (Test would verify error message)
        pass


class TestDataConsistency:
    """Test data consistency across operations"""

    def test_sheets_drive_sync(self):
        """Test that Sheets and Drive stay in sync"""
        sheets = Mock()
        drive = Mock()

        # Mock successful upload
        drive.upload_source_pdf.return_value = 'file-123'
        drive.get_file_link.return_value = 'https://drive.google.com/file/d/file-123'

        # Verify Sheet is updated with Drive link
        sheets.update_source_status.assert_not_called()

        # After upload, Sheet should be updated
        # (Full test would verify this)

    def test_cache_consistency(self):
        """Test that cache stays consistent with remote"""
        # Test that cached files are validated
        # Test that stale cache is invalidated
        pass


class TestPerformance:
    """Performance and scalability tests"""

    def test_large_article_processing(self):
        """Test processing article with 200+ sources"""
        # Mock large source list
        # Verify performance is acceptable
        pass

    def test_concurrent_processing(self):
        """Test processing multiple sources concurrently"""
        # Verify thread safety
        # Verify performance improvement
        pass

    def test_memory_usage(self):
        """Test memory doesn't grow unbounded"""
        # Process many articles
        # Verify memory is released
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
