#!/usr/bin/env python3
"""
Stanford Law Review Sourcepull System
Complete workflow for retrieving and redboxing legal sources
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.stage1.enhanced_source_retriever import EnhancedSourceRetriever, RetrievalResult
from src.stage1.pdf_redboxer import PDFRedboxer, RedboxResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sourcepull_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SourcepullConfig:
    """Configuration for the sourcepull system"""
    output_dir: str = "./data/Sourcepull"
    cache_dir: str = "./cache"
    apis: Dict[str, str] = None
    redbox_enabled: bool = True
    create_summary_report: bool = True
    
    def __post_init__(self):
        if self.apis is None:
            self.apis = {}


class SourcepullSystem:
    """Complete sourcepull system for Stanford Law Review"""
    
    def __init__(self, config: SourcepullConfig):
        self.config = config
        
        # Create directories
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize components
        self.retriever = EnhancedSourceRetriever({
            'output_dir': config.output_dir,
            'cache_dir': config.cache_dir,
            'apis': config.apis
        })
        
        if config.redbox_enabled:
            self.redboxer = PDFRedboxer({
                'output_dir': config.output_dir
            })
        
        # Statistics
        self.session_stats = {
            'session_start': datetime.now(),
            'total_sources': 0,
            'retrieved_successfully': 0,
            'retrieval_failed': 0,
            'redboxed_successfully': 0,
            'redboxing_failed': 0,
            'manual_review_required': 0
        }
    
    def run_sherkow_gugliuzza_sourcepull(self) -> Dict[str, Any]:
        """Run the complete sourcepull process for Sherkow & Gugliuzza article"""
        
        logger.info("="*80)
        logger.info("STARTING STANFORD LAW REVIEW SOURCEPULL SYSTEM")
        logger.info("Article: Sherkow & Gugliuzza Patent Law Citations")
        logger.info("="*80)
        
        try:
            # Step 1: Retrieve all source documents
            logger.info("\nSTEP 1: RETRIEVING SOURCE DOCUMENTS")
            logger.info("-" * 50)
            
            retrieval_results = self.retriever.retrieve_sherkow_gugliuzza_sources()
            
            self.session_stats['total_sources'] = len(retrieval_results)
            self.session_stats['retrieved_successfully'] = len([r for r in retrieval_results if r.status == "success"])
            self.session_stats['retrieval_failed'] = len([r for r in retrieval_results if r.status == "failed"])
            
            self._log_retrieval_results(retrieval_results)
            
            # Step 2: Apply redboxing if enabled
            redbox_results = []
            if self.config.redbox_enabled:
                logger.info("\nSTEP 2: APPLYING REDBOXING TO RETRIEVED DOCUMENTS")
                logger.info("-" * 50)
                
                redbox_results = self.redboxer.redbox_sherkow_gugliuzza_documents(retrieval_results)
                
                self.session_stats['redboxed_successfully'] = len([r for r in redbox_results if r.status == "success"])
                self.session_stats['redboxing_failed'] = len([r for r in redbox_results if r.status == "failed"])
                self.session_stats['manual_review_required'] = len([r for r in redbox_results if r.status in ["partial", "manual_required"]])
                
                self._log_redboxing_results(redbox_results)
            
            # Step 3: Generate summary reports
            if self.config.create_summary_report:
                logger.info("\nSTEP 3: GENERATING SUMMARY REPORTS")
                logger.info("-" * 50)
                
                summary_data = self._create_comprehensive_summary(retrieval_results, redbox_results)
                
                # Write summary report
                self._write_summary_report(summary_data, retrieval_results, redbox_results)
                
                if redbox_results:
                    # Create detailed redboxing summary
                    redbox_summary_path = self.redboxer.create_redbox_summary_report(redbox_results)
                    logger.info(f"Redboxing summary report: {redbox_summary_path}")
            
            # Step 4: Final session summary
            self._print_session_summary()
            
            return {
                'status': 'completed',
                'session_stats': self.session_stats,
                'retrieval_results': retrieval_results,
                'redbox_results': redbox_results,
                'summary_data': summary_data if self.config.create_summary_report else None
            }
        
        except Exception as e:
            logger.error(f"Sourcepull system error: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'session_stats': self.session_stats
            }
    
    def _log_retrieval_results(self, results: List[RetrievalResult]):
        """Log detailed retrieval results"""
        
        for result in results:
            status_symbol = {
                'success': '✅',
                'partial': '⚠️',
                'failed': '❌',
                'manual_required': '📝'
            }.get(result.status, '❓')
            
            logger.info(f"{status_symbol} {result.source_id}: {result.message}")
            
            if result.status == "success":
                logger.info(f"   📄 File: {Path(result.file_path).name}")
                logger.info(f"   🔗 Source: {result.source_url}")
                if result.redbox_elements:
                    logger.info(f"   🎯 Redbox elements: {len(result.redbox_elements)}")
            
            elif result.status in ["failed", "manual_required"]:
                logger.warning(f"   ⚠️  Manual intervention required: {result.message}")
    
    def _log_redboxing_results(self, results: List[RedboxResult]):
        """Log detailed redboxing results"""
        
        for result in results:
            status_symbol = {
                'success': '✅',
                'partial': '⚠️',
                'failed': '❌',
                'manual_required': '📝'
            }.get(result.status, '❓')
            
            logger.info(f"{status_symbol} {result.source_id}: {result.message}")
            
            if result.total_boxes_drawn > 0:
                logger.info(f"   🔴 Red boxes applied: {result.total_boxes_drawn}")
                logger.info(f"   ✅ Elements found: {len(result.elements_found)}")
                
                if result.elements_not_found:
                    logger.warning(f"   ❌ Elements not found: {len(result.elements_not_found)}")
                    for element in result.elements_not_found[:3]:  # Show first 3
                        logger.warning(f"      - {element['element_type']}: {element['text'][:40]}...")
            
            if result.status == "success":
                logger.info(f"   📄 Redboxed file: {Path(result.redboxed_file).name}")
    
    def _create_comprehensive_summary(self, retrieval_results: List[RetrievalResult], 
                                    redbox_results: List[RedboxResult]) -> Dict[str, Any]:
        """Create comprehensive summary data"""
        
        summary = {
            'session_info': {
                'timestamp': datetime.now().isoformat(),
                'article': 'Sherkow & Gugliuzza Patent Law Citations',
                'system_version': '2.0',
                'output_directory': self.config.output_dir
            },
            'retrieval_summary': {
                'total_sources': len(retrieval_results),
                'successful': len([r for r in retrieval_results if r.status == "success"]),
                'partial': len([r for r in retrieval_results if r.status == "partial"]),
                'failed': len([r for r in retrieval_results if r.status in ["failed", "manual_required"]]),
                'pdfs_retrieved': len([r for r in retrieval_results if r.file_type == "pdf"]),
                'html_retrieved': len([r for r in retrieval_results if r.file_type == "html"]),
                'cache_hits': self.retriever.get_retrieval_stats().get('cached_hits', 0)
            },
            'redboxing_summary': {
                'enabled': self.config.redbox_enabled,
                'documents_processed': len(redbox_results),
                'successful': len([r for r in redbox_results if r.status == "success"]),
                'partial': len([r for r in redbox_results if r.status == "partial"]),
                'failed': len([r for r in redbox_results if r.status in ["failed", "manual_required"]]),
                'total_boxes_applied': sum(r.total_boxes_drawn for r in redbox_results),
                'manual_review_required': len([r for r in redbox_results if r.requires_manual_review or r.status in ["partial", "manual_required"]])
            } if self.config.redbox_enabled else None,
            'source_details': [],
            'recommendations': []
        }
        
        # Add detailed source information
        for i, retrieval_result in enumerate(retrieval_results):
            source_detail = {
                'source_id': retrieval_result.source_id,
                'citation': retrieval_results[i].metadata.get('citation', 'Unknown') if hasattr(retrieval_results[i], 'metadata') else 'Unknown',
                'retrieval_status': retrieval_result.status,
                'file_type': retrieval_result.file_type,
                'file_path': retrieval_result.file_path,
                'source_url': retrieval_result.source_url
            }
            
            # Add redboxing info if available
            if self.config.redbox_enabled and i < len(redbox_results):
                redbox_result = redbox_results[i]
                source_detail['redboxing'] = {
                    'status': redbox_result.status,
                    'boxes_applied': redbox_result.total_boxes_drawn,
                    'elements_found': len(redbox_result.elements_found),
                    'elements_missing': len(redbox_result.elements_not_found),
                    'redboxed_file': redbox_result.redboxed_file
                }
            
            summary['source_details'].append(source_detail)
        
        # Generate recommendations
        summary['recommendations'] = self._generate_recommendations(retrieval_results, redbox_results)
        
        return summary
    
    def _generate_recommendations(self, retrieval_results: List[RetrievalResult], 
                                 redbox_results: List[RedboxResult]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Retrieval recommendations
        failed_retrievals = [r for r in retrieval_results if r.status in ["failed", "manual_required"]]
        if failed_retrievals:
            recommendations.append(f"Manual retrieval required for {len(failed_retrievals)} source(s): " +
                                 ", ".join([r.source_id for r in failed_retrievals]))
        
        partial_retrievals = [r for r in retrieval_results if r.status == "partial"]
        if partial_retrievals:
            recommendations.append(f"Review partial retrievals for {len(partial_retrievals)} source(s) - may need better quality PDFs")
        
        # Redboxing recommendations
        if self.config.redbox_enabled:
            manual_redbox = [r for r in redbox_results if r.status in ["manual_required", "partial"]]
            if manual_redbox:
                recommendations.append(f"Manual redboxing review required for {len(manual_redbox)} document(s)")
            
            missing_elements = sum(len(r.elements_not_found) for r in redbox_results)
            if missing_elements > 0:
                recommendations.append(f"Manually locate {missing_elements} citation elements that automated redboxing could not find")
        
        # Quality recommendations
        pdf_count = len([r for r in retrieval_results if r.file_type == "pdf"])
        if pdf_count < len(retrieval_results):
            recommendations.append("Consider converting HTML sources to PDF for better redboxing results")
        
        # General recommendations
        recommendations.append("Review all redboxed documents for citation accuracy")
        recommendations.append("Verify all quotes match exactly with source text")
        recommendations.append("Check page numbers and years for any discrepancies")
        
        return recommendations
    
    def _write_summary_report(self, summary_data: Dict[str, Any], 
                             retrieval_results: List[RetrievalResult],
                             redbox_results: List[RedboxResult]):
        """Write comprehensive summary report"""
        
        output_dir = Path(self.config.output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON summary
        json_path = output_dir / f"sourcepull_summary_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        # Human-readable report
        report_path = output_dir / f"sourcepull_report_{timestamp}.txt"
        
        report = f"""STANFORD LAW REVIEW - SOURCEPULL SYSTEM REPORT
Generated: {summary_data['session_info']['timestamp']}
Article: {summary_data['session_info']['article']}

EXECUTIVE SUMMARY
=================
Total Sources: {summary_data['retrieval_summary']['total_sources']}
Successfully Retrieved: {summary_data['retrieval_summary']['successful']} PDFs, {summary_data['retrieval_summary']['html_retrieved']} HTML files
Failed Retrievals: {summary_data['retrieval_summary']['failed']}
"""
        
        if summary_data['redboxing_summary']:
            report += f"""
REDBOXING RESULTS
================
Documents Processed: {summary_data['redboxing_summary']['documents_processed']}
Successfully Redboxed: {summary_data['redboxing_summary']['successful']}
Total Red Boxes Applied: {summary_data['redboxing_summary']['total_boxes_applied']}
Manual Review Required: {summary_data['redboxing_summary']['manual_review_required']}
"""
        
        report += f"""
DETAILED SOURCE BREAKDOWN
=========================
"""
        
        for source in summary_data['source_details']:
            report += f"\nSource ID: {source['source_id']}\n"
            report += f"Retrieval: {source['retrieval_status'].upper()}\n"
            report += f"File Type: {source['file_type']}\n"
            
            if source.get('file_path'):
                report += f"File: {Path(source['file_path']).name}\n"
            
            if source.get('redboxing'):
                rb = source['redboxing']
                report += f"Redboxing: {rb['status'].upper()} ({rb['boxes_applied']} boxes)\n"
                if rb['elements_missing'] > 0:
                    report += f"Missing Elements: {rb['elements_missing']}\n"
            
            report += "-" * 40 + "\n"
        
        report += f"""
RECOMMENDATIONS
===============
"""
        for i, rec in enumerate(summary_data['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
FILES CREATED
=============
• JSON Summary: {json_path.name}
• Text Report: {report_path.name}
• All retrieved sources in: {output_dir}/
"""
        
        if summary_data['redboxing_summary'] and summary_data['redboxing_summary']['enabled']:
            report += f"• Redboxed PDFs in: {output_dir}/Redboxed/\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Summary reports created:")
        logger.info(f"  📊 JSON: {json_path}")
        logger.info(f"  📄 Report: {report_path}")
    
    def _print_session_summary(self):
        """Print final session summary"""
        
        logger.info("\n" + "="*80)
        logger.info("SOURCEPULL SESSION COMPLETE")
        logger.info("="*80)
        
        stats = self.session_stats
        
        logger.info(f"📊 SESSION STATISTICS:")
        logger.info(f"   Total Sources: {stats['total_sources']}")
        logger.info(f"   Retrieved Successfully: {stats['retrieved_successfully']}")
        logger.info(f"   Retrieval Failed: {stats['retrieval_failed']}")
        
        if self.config.redbox_enabled:
            logger.info(f"   Redboxed Successfully: {stats['redboxed_successfully']}")
            logger.info(f"   Manual Review Required: {stats['manual_review_required']}")
        
        session_duration = datetime.now() - stats['session_start']
        logger.info(f"   Session Duration: {session_duration}")
        
        logger.info(f"\n📁 OUTPUT LOCATION: {Path(self.config.output_dir).absolute()}")
        
        if stats['manual_review_required'] > 0:
            logger.warning(f"\n⚠️  ATTENTION: {stats['manual_review_required']} document(s) require manual editorial review")
        
        logger.info("\n✅ Sourcepull system completed successfully!")


def load_api_config() -> Dict[str, str]:
    """Load API configuration from environment variables or config file"""
    
    apis = {}
    
    # Try to load from environment variables
    api_keys = {
        'courtlistener': os.getenv('COURTLISTENER_API_KEY'),
        'govinfo': os.getenv('GOVINFO_API_KEY'),
        'justia': os.getenv('JUSTIA_API_KEY'),
        'google_books': os.getenv('GOOGLE_BOOKS_API_KEY'),
        'crossref': os.getenv('CROSSREF_API_KEY')
    }
    
    # Filter out None values
    apis = {k: v for k, v in api_keys.items() if v}
    
    # Try to load from config file
    config_file = Path('config/api_keys.json')
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_apis = json.load(f)
                apis.update(file_apis)
        except Exception as e:
            logger.warning(f"Could not load API config file: {e}")
    
    if apis:
        logger.info(f"Loaded API keys for: {', '.join(apis.keys())}")
    else:
        logger.warning("No API keys configured - will use free sources only")
    
    return apis


def main():
    """Main entry point"""
    
    # Load configuration
    apis = load_api_config()
    
    config = SourcepullConfig(
        output_dir="./data/Sourcepull",
        cache_dir="./cache",
        apis=apis,
        redbox_enabled=True,
        create_summary_report=True
    )
    
    # Initialize and run system
    system = SourcepullSystem(config)
    result = system.run_sherkow_gugliuzza_sourcepull()
    
    # Return appropriate exit code
    if result['status'] == 'completed':
        return 0
    else:
        logger.error(f"System failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())