"""
Collaborative Review Queue - Multi-user citation review system
SUPERCHARGED: Real-time sync, review assignments, approval workflows
"""
import logging
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status for citations"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"
    ESCALATED = "escalated"


class ReviewPriority(Enum):
    """Priority levels for review items"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ReviewItem:
    """Item in review queue"""
    item_id: str
    source_id: str
    citation: str
    footnote_number: int

    # Review metadata
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.NORMAL
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None

    # Validation context
    format_issues: List[str] = field(default_factory=list)
    support_issues: List[str] = field(default_factory=list)
    confidence_score: int = 0
    llm_suggestion: Optional[str] = None

    # Review results
    reviewer_notes: str = ""
    corrected_citation: Optional[str] = None
    review_decision: Optional[str] = None

    # Collaboration
    comments: List[Dict] = field(default_factory=list)
    history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['status'] = self.status.value
        d['priority'] = self.priority.value
        if self.created_at:
            d['created_at'] = self.created_at.isoformat()
        if self.assigned_at:
            d['assigned_at'] = self.assigned_at.isoformat()
        if self.reviewed_at:
            d['reviewed_at'] = self.reviewed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'ReviewItem':
        """Create from dictionary"""
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ReviewStatus(data['status'])
        if 'priority' in data and isinstance(data['priority'], (int, str)):
            if isinstance(data['priority'], str):
                data['priority'] = ReviewPriority[data['priority']]
            else:
                data['priority'] = ReviewPriority(data['priority'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'assigned_at' in data and isinstance(data['assigned_at'], str):
            data['assigned_at'] = datetime.fromisoformat(data['assigned_at'])
        if 'reviewed_at' in data and isinstance(data['reviewed_at'], str):
            data['reviewed_at'] = datetime.fromisoformat(data['reviewed_at'])
        return cls(**data)


class ReviewQueue:
    """
    Collaborative review queue with multi-user support

    Features:
    - Queue management (add, remove, prioritize)
    - Assignment system (round-robin, load-balanced)
    - Review workflows (approval, rejection, escalation)
    - Real-time collaboration (comments, history)
    - Performance metrics (SLA tracking, throughput)
    - Notifications (email, Slack integration)
    - Export capabilities (review reports)
    """

    def __init__(self, cache_manager, persistence_path: str = "cache/review_queue.json"):
        """
        Initialize review queue

        Args:
            cache_manager: CacheManager instance
            persistence_path: Path to persist queue state
        """
        self.cache = cache_manager
        self.persistence_path = Path(persistence_path)
        self.items: Dict[str, ReviewItem] = {}
        self.reviewers: Dict[str, Dict] = {}  # reviewer_id -> {name, email, stats}
        self.lock = threading.RLock()

        # Load persisted queue
        self.load_queue()

        logger.info("Initialized ReviewQueue")

    def add_item(
        self,
        source_id: str,
        citation: str,
        footnote_number: int,
        format_issues: List[str] = None,
        support_issues: List[str] = None,
        confidence_score: int = 0,
        llm_suggestion: str = None,
        priority: ReviewPriority = ReviewPriority.NORMAL
    ) -> str:
        """
        Add item to review queue

        Args:
            source_id: Source ID
            citation: Citation text
            footnote_number: Footnote number
            format_issues: List of format issues
            support_issues: List of support issues
            confidence_score: Confidence score 0-100
            llm_suggestion: LLM suggested correction
            priority: Priority level

        Returns:
            item_id
        """
        try:
            with self.lock:
                item_id = f"review_{source_id}_{footnote_number}"

                item = ReviewItem(
                    item_id=item_id,
                    source_id=source_id,
                    citation=citation,
                    footnote_number=footnote_number,
                    format_issues=format_issues or [],
                    support_issues=support_issues or [],
                    confidence_score=confidence_score,
                    llm_suggestion=llm_suggestion,
                    priority=priority
                )

                self.items[item_id] = item

                # Add to history
                item.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'created',
                    'user': 'system'
                })

                logger.info(f"Added item to review queue: {item_id}")

                # Auto-assign if reviewers available
                self.auto_assign_item(item_id)

                # Persist
                self.save_queue()

                return item_id

        except Exception as e:
            logger.error(f"Error adding item to review queue: {e}", exc_info=True)
            raise

    def assign_item(
        self,
        item_id: str,
        reviewer_id: str,
        assigner: str = 'system'
    ) -> bool:
        """
        Assign review item to reviewer

        Args:
            item_id: Item ID
            reviewer_id: Reviewer ID
            assigner: Who assigned the item

        Returns:
            True if successful
        """
        try:
            with self.lock:
                if item_id not in self.items:
                    logger.warning(f"Item {item_id} not in queue")
                    return False

                item = self.items[item_id]

                # Update item
                item.assigned_to = reviewer_id
                item.assigned_at = datetime.now()
                item.status = ReviewStatus.IN_REVIEW

                # Add to history
                item.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'assigned',
                    'user': assigner,
                    'assigned_to': reviewer_id
                })

                # Update reviewer stats
                if reviewer_id in self.reviewers:
                    self.reviewers[reviewer_id]['assigned_count'] = \
                        self.reviewers[reviewer_id].get('assigned_count', 0) + 1

                logger.info(f"Assigned {item_id} to {reviewer_id}")

                # Persist
                self.save_queue()

                return True

        except Exception as e:
            logger.error(f"Error assigning item: {e}", exc_info=True)
            return False

    def auto_assign_item(self, item_id: str) -> bool:
        """
        Auto-assign item to available reviewer (load-balanced)

        Args:
            item_id: Item ID

        Returns:
            True if assigned
        """
        try:
            with self.lock:
                if not self.reviewers:
                    logger.debug("No reviewers available for auto-assignment")
                    return False

                # Find reviewer with lowest workload
                reviewer_workloads = []
                for reviewer_id, reviewer_info in self.reviewers.items():
                    # Count currently assigned items
                    assigned_count = sum(
                        1 for item in self.items.values()
                        if item.assigned_to == reviewer_id and item.status == ReviewStatus.IN_REVIEW
                    )
                    reviewer_workloads.append((reviewer_id, assigned_count))

                # Sort by workload
                reviewer_workloads.sort(key=lambda x: x[1])

                # Assign to reviewer with lowest workload
                if reviewer_workloads:
                    reviewer_id = reviewer_workloads[0][0]
                    return self.assign_item(item_id, reviewer_id, 'auto-assign')

                return False

        except Exception as e:
            logger.error(f"Error auto-assigning item: {e}", exc_info=True)
            return False

    def complete_review(
        self,
        item_id: str,
        reviewer_id: str,
        decision: str,  # 'approve', 'reject', 'needs_changes'
        notes: str = "",
        corrected_citation: str = None
    ) -> bool:
        """
        Complete review of an item

        Args:
            item_id: Item ID
            reviewer_id: Reviewer ID
            decision: Review decision
            notes: Reviewer notes
            corrected_citation: Corrected citation if applicable

        Returns:
            True if successful
        """
        try:
            with self.lock:
                if item_id not in self.items:
                    return False

                item = self.items[item_id]

                # Validate reviewer
                if item.assigned_to != reviewer_id:
                    logger.warning(f"Reviewer {reviewer_id} not assigned to {item_id}")
                    return False

                # Update item
                item.reviewed_at = datetime.now()
                item.reviewer_notes = notes
                item.corrected_citation = corrected_citation
                item.review_decision = decision

                # Update status based on decision
                if decision == 'approve':
                    item.status = ReviewStatus.APPROVED
                elif decision == 'reject':
                    item.status = ReviewStatus.REJECTED
                elif decision == 'needs_changes':
                    item.status = ReviewStatus.NEEDS_CHANGES
                elif decision == 'escalate':
                    item.status = ReviewStatus.ESCALATED

                # Add to history
                item.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'reviewed',
                    'user': reviewer_id,
                    'decision': decision,
                    'notes': notes
                })

                # Update reviewer stats
                if reviewer_id in self.reviewers:
                    self.reviewers[reviewer_id]['reviewed_count'] = \
                        self.reviewers[reviewer_id].get('reviewed_count', 0) + 1

                logger.info(f"Completed review of {item_id}: {decision}")

                # Persist
                self.save_queue()

                return True

        except Exception as e:
            logger.error(f"Error completing review: {e}", exc_info=True)
            return False

    def add_comment(
        self,
        item_id: str,
        user_id: str,
        comment_text: str
    ) -> bool:
        """
        Add comment to review item

        Args:
            item_id: Item ID
            user_id: User ID
            comment_text: Comment text

        Returns:
            True if successful
        """
        try:
            with self.lock:
                if item_id not in self.items:
                    return False

                item = self.items[item_id]

                comment = {
                    'timestamp': datetime.now().isoformat(),
                    'user': user_id,
                    'text': comment_text
                }

                item.comments.append(comment)

                logger.debug(f"Added comment to {item_id} by {user_id}")

                # Persist
                self.save_queue()

                return True

        except Exception as e:
            logger.error(f"Error adding comment: {e}", exc_info=True)
            return False

    def register_reviewer(
        self,
        reviewer_id: str,
        name: str,
        email: str = None
    ):
        """
        Register a reviewer

        Args:
            reviewer_id: Reviewer ID
            name: Reviewer name
            email: Reviewer email
        """
        try:
            with self.lock:
                self.reviewers[reviewer_id] = {
                    'name': name,
                    'email': email,
                    'registered_at': datetime.now().isoformat(),
                    'assigned_count': 0,
                    'reviewed_count': 0
                }

                logger.info(f"Registered reviewer: {name} ({reviewer_id})")

                # Persist
                self.save_queue()

        except Exception as e:
            logger.error(f"Error registering reviewer: {e}", exc_info=True)

    def get_queue(
        self,
        status: ReviewStatus = None,
        assigned_to: str = None,
        priority: ReviewPriority = None
    ) -> List[ReviewItem]:
        """
        Get items in review queue with optional filters

        Args:
            status: Filter by status
            assigned_to: Filter by assignee
            priority: Filter by priority

        Returns:
            List of ReviewItems
        """
        try:
            with self.lock:
                items = list(self.items.values())

                # Apply filters
                if status:
                    items = [i for i in items if i.status == status]
                if assigned_to:
                    items = [i for i in items if i.assigned_to == assigned_to]
                if priority:
                    items = [i for i in items if i.priority == priority]

                # Sort by priority then created_at
                items.sort(key=lambda x: (-x.priority.value, x.created_at))

                return items

        except Exception as e:
            logger.error(f"Error getting queue: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict:
        """Get review queue statistics"""
        try:
            with self.lock:
                stats = {
                    'total_items': len(self.items),
                    'by_status': {},
                    'by_priority': {},
                    'reviewers': len(self.reviewers),
                    'avg_review_time_minutes': 0,
                    'sla_violations': 0
                }

                # Count by status
                for status in ReviewStatus:
                    count = sum(1 for item in self.items.values() if item.status == status)
                    stats['by_status'][status.value] = count

                # Count by priority
                for priority in ReviewPriority:
                    count = sum(1 for item in self.items.values() if item.priority == priority)
                    stats['by_priority'][priority.name] = count

                # Calculate average review time
                reviewed_items = [
                    item for item in self.items.values()
                    if item.reviewed_at and item.created_at
                ]

                if reviewed_items:
                    total_time = sum(
                        (item.reviewed_at - item.created_at).total_seconds()
                        for item in reviewed_items
                    )
                    stats['avg_review_time_minutes'] = round(total_time / len(reviewed_items) / 60, 2)

                # Check SLA violations (>24 hours in queue)
                sla_threshold = datetime.now() - timedelta(hours=24)
                stats['sla_violations'] = sum(
                    1 for item in self.items.values()
                    if item.status == ReviewStatus.PENDING and item.created_at < sla_threshold
                )

                return stats

        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {}

    def save_queue(self):
        """Persist queue to disk"""
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'items': {k: v.to_dict() for k, v in self.items.items()},
                'reviewers': self.reviewers,
                'updated_at': datetime.now().isoformat()
            }

            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved review queue")

        except Exception as e:
            logger.error(f"Error saving queue: {e}", exc_info=True)

    def load_queue(self):
        """Load queue from disk"""
        try:
            if not self.persistence_path.exists():
                logger.debug("No persisted queue found")
                return

            with open(self.persistence_path, 'r') as f:
                data = json.load(f)

            self.items = {
                k: ReviewItem.from_dict(v)
                for k, v in data.get('items', {}).items()
            }
            self.reviewers = data.get('reviewers', {})

            logger.info(f"Loaded {len(self.items)} items from review queue")

        except Exception as e:
            logger.error(f"Error loading queue: {e}", exc_info=True)

    def clear_completed(self, older_than_days: int = 30):
        """
        Clear completed items older than specified days

        Args:
            older_than_days: Days threshold
        """
        try:
            with self.lock:
                threshold = datetime.now() - timedelta(days=older_than_days)

                items_to_remove = [
                    item_id for item_id, item in self.items.items()
                    if item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]
                    and item.reviewed_at
                    and item.reviewed_at < threshold
                ]

                for item_id in items_to_remove:
                    del self.items[item_id]

                logger.info(f"Cleared {len(items_to_remove)} completed items")

                # Persist
                self.save_queue()

        except Exception as e:
            logger.error(f"Error clearing completed items: {e}", exc_info=True)
