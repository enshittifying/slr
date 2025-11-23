"""
Data models for type safety and structure
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class PipelineStage(Enum):
    """Pipeline processing stages"""
    NOT_STARTED = "not_started"
    SP_IN_PROGRESS = "sp_in_progress"
    SP_COMPLETE = "sp_complete"
    SP_ERROR = "sp_error"
    R1_IN_PROGRESS = "r1_in_progress"
    R1_COMPLETE = "r1_complete"
    R1_ERROR = "r1_error"
    R2_IN_PROGRESS = "r2_in_progress"
    R2_COMPLETE = "r2_complete"
    R2_ERROR = "r2_error"
    COMPLETE = "complete"


class SourceType(Enum):
    """Types of legal sources"""
    CASE = "case"
    STATUTE = "statute"
    ARTICLE = "article"
    BOOK = "book"
    REGULATION = "regulation"
    TREATISE = "treatise"
    RESTATEMENT = "restatement"
    LEGISLATIVE_HISTORY = "legislative_history"
    UNPUBLISHED = "unpublished"
    OTHER = "other"


class SourceStatus(Enum):
    """Status of source retrieval/processing"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    ERROR = "error"
    SKIPPED = "skipped"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class Article:
    """Represents a law review article being processed"""
    article_id: str
    volume_issue: str
    author: str
    title: str
    stage: PipelineStage = PipelineStage.NOT_STARTED
    drive_link: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['stage'] = self.stage.value
        if self.created_at:
            d['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            d['updated_at'] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'Article':
        """Create from dictionary"""
        if 'stage' in data and isinstance(data['stage'], str):
            data['stage'] = PipelineStage(data['stage'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class Source:
    """Represents a legal source cited in an article"""
    source_id: str
    article_id: str
    citation: str
    source_type: SourceType
    footnote_number: Optional[int] = None
    status: SourceStatus = SourceStatus.PENDING
    drive_link: Optional[str] = None
    r1_drive_link: Optional[str] = None
    database: Optional[str] = None  # HeinOnline, Westlaw, etc.
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['source_type'] = self.source_type.value
        d['status'] = self.status.value
        if self.created_at:
            d['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            d['updated_at'] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'Source':
        """Create from dictionary"""
        if 'source_type' in data and isinstance(data['source_type'], str):
            data['source_type'] = SourceType(data['source_type'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = SourceStatus(data['status'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class Citation:
    """Represents a parsed citation"""
    full_text: str
    citation_type: SourceType
    components: Dict = field(default_factory=dict)

    # Case-specific fields
    party1: Optional[str] = None
    party2: Optional[str] = None
    reporter: Optional[str] = None

    # Common fields
    volume: Optional[str] = None
    page: Optional[str] = None
    year: Optional[str] = None
    pincite: Optional[str] = None

    # Article-specific fields
    author: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None

    # Statute-specific fields
    statute_title: Optional[str] = None
    section: Optional[str] = None
    code: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['citation_type'] = self.citation_type.value
        return d


@dataclass
class ValidationResult:
    """Results from LLM validation"""
    source_id: str
    citation: str
    footnote_number: int

    # Format validation
    format_issues: List[str] = field(default_factory=list)
    format_suggestion: Optional[str] = None

    # Support validation
    support_issues: List[str] = field(default_factory=list)
    confidence_score: int = 0  # 0-100

    # Review flag
    requires_review: bool = False
    review_reason: Optional[str] = None

    # Source text analyzed
    proposition: Optional[str] = None
    source_text: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationResult':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ProcessingResult:
    """Results from a processing stage"""
    stage: PipelineStage
    article_id: str
    success_count: int = 0
    fail_count: int = 0
    total: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['stage'] = self.stage.value
        if self.start_time:
            d['start_time'] = self.start_time.isoformat()
        if self.end_time:
            d['end_time'] = self.end_time.isoformat()
        return d

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ArticleState:
    """Complete state of an article in the pipeline"""
    article: Article
    sources: List[Source] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    processing_history: List[ProcessingResult] = field(default_factory=list)

    def get_sources_by_status(self, status: SourceStatus) -> List[Source]:
        """Filter sources by status"""
        return [s for s in self.sources if s.status == status]

    def get_sources_by_type(self, source_type: SourceType) -> List[Source]:
        """Filter sources by type"""
        return [s for s in self.sources if s.source_type == source_type]

    def get_validation_issues_count(self) -> int:
        """Count total validation issues"""
        return sum(len(v.format_issues) + len(v.support_issues) for v in self.validation_results)

    def get_review_queue_count(self) -> int:
        """Count items requiring review"""
        return sum(1 for v in self.validation_results if v.requires_review)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'article': self.article.to_dict(),
            'sources': [s.to_dict() for s in self.sources],
            'validation_results': [v.to_dict() for v in self.validation_results],
            'processing_history': [p.to_dict() for p in self.processing_history]
        }


@dataclass
class Credentials:
    """Encrypted credentials configuration"""
    encrypted_path: str
    service_account_email: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary (excludes API keys for security)"""
        return {
            'encrypted_path': self.encrypted_path,
            'service_account_email': self.service_account_email
        }


@dataclass
class AppConfig:
    """Application configuration"""
    # Google Drive/Sheets
    spreadsheet_id: str
    drive_folder_id: str

    # LLM Configuration
    llm_provider: str = "openai"  # "openai" or "anthropic"
    llm_model: str = "gpt-4o-mini"

    # Processing settings
    max_concurrent_downloads: int = 5
    retry_attempts: int = 3
    timeout_seconds: int = 30

    # Cache settings
    cache_dir: str = "cache"
    output_dir: str = "output"

    # UI settings
    theme: str = "light"
    window_size: tuple = (1200, 800)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['window_size'] = list(self.window_size)
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        """Create from dictionary"""
        if 'window_size' in data and isinstance(data['window_size'], list):
            data['window_size'] = tuple(data['window_size'])
        return cls(**data)


# Type aliases for clarity
ArticleID = str
SourceID = str
FootnoteNumber = int
