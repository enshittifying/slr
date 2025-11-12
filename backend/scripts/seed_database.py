"""Seed database with test data."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Article, Citation, Task, TaskAssignment, User


async def seed_data():
    """Seed database with test data."""
    async with AsyncSessionLocal() as db:
        # Check if data already exists
        result = await db.execute(select(User))
        if result.scalars().first():
            print("✓ Database already seeded, skipping...")
            return

        print("Seeding database...")

        # Create users
        admin = User(
            id=uuid.uuid4(),
            email="admin@stanford.edu",
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
        db.add(admin)

        senior_editor = User(
            id=uuid.uuid4(),
            email="senior@stanford.edu",
            full_name="Senior Editor",
            role="senior_editor",
            is_active=True,
        )
        db.add(senior_editor)

        member1 = User(
            id=uuid.uuid4(),
            email="member1@stanford.edu",
            full_name="Member Editor 1",
            role="member_editor",
            is_active=True,
        )
        db.add(member1)

        member2 = User(
            id=uuid.uuid4(),
            email="member2@stanford.edu",
            full_name="Member Editor 2",
            role="member_editor",
            is_active=True,
        )
        db.add(member2)

        await db.commit()
        print("✓ Created 4 users")

        # Create tasks
        task1 = Task(
            id=uuid.uuid4(),
            title="Review Article Submission #123",
            description="Perform initial substantive review",
            due_date=datetime.utcnow() + timedelta(days=7),
            created_by=admin.id,
        )
        db.add(task1)

        task2 = Task(
            id=uuid.uuid4(),
            title="Complete R2 validation for Volume 79",
            description="Review all citations requiring manual review",
            due_date=datetime.utcnow() + timedelta(days=14),
            created_by=senior_editor.id,
        )
        db.add(task2)

        await db.commit()
        print("✓ Created 2 tasks")

        # Create task assignments
        assignment1 = TaskAssignment(
            id=uuid.uuid4(),
            task_id=task1.id,
            user_id=member1.id,
            status="in_progress",
        )
        db.add(assignment1)

        assignment2 = TaskAssignment(
            id=uuid.uuid4(),
            task_id=task2.id,
            user_id=member2.id,
            status="not_started",
        )
        db.add(assignment2)

        await db.commit()
        print("✓ Created 2 task assignments")

        # Create articles
        article1 = Article(
            id=uuid.uuid4(),
            title="The Future of AI in Legal Research",
            author_name="Jane Smith",
            volume_number=79,
            issue_number=1,
            status="r2_in_progress",
            assigned_editor=senior_editor.id,
            submitted_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(article1)

        article2 = Article(
            id=uuid.uuid4(),
            title="Constitutional Challenges in Digital Privacy",
            author_name="John Doe",
            volume_number=79,
            issue_number=1,
            status="draft",
            assigned_editor=member1.id,
            submitted_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(article2)

        await db.commit()
        print("✓ Created 2 articles")

        # Create citations for article1
        for i in range(1, 11):
            citation = Citation(
                id=uuid.uuid4(),
                article_id=article1.id,
                footnote_number=i,
                citation_text=f"Sample Citation {i}, 123 U.S. 456 (2020).",
                proposition=f"This case establishes principle {i}.",
                source_type="case",
                source_title=f"Sample v. Citation {i}",
                sp_status="completed",
                r1_status="completed",
                r2_status="completed" if i <= 8 else "manual_required",
                format_valid=True,
                support_valid=True if i <= 8 else False,
                quote_valid=True,
                requires_manual_review=i > 8,
            )
            db.add(citation)

        # Create citations for article2
        for i in range(1, 6):
            citation = Citation(
                id=uuid.uuid4(),
                article_id=article2.id,
                footnote_number=i,
                citation_text=f"Another Citation {i}, 789 F.3d 123 (9th Cir. 2021).",
                proposition=f"The court held that {i}...",
                source_type="case",
                sp_status="pending",
                r1_status="pending",
                r2_status="pending",
            )
            db.add(citation)

        await db.commit()
        print("✓ Created 15 citations")

        print("\n✅ Database seeded successfully!")
        print("\nTest credentials:")
        print("  Admin:        admin@stanford.edu")
        print("  Senior Editor: senior@stanford.edu")
        print("  Member 1:      member1@stanford.edu")
        print("  Member 2:      member2@stanford.edu")


if __name__ == "__main__":
    asyncio.run(seed_data())
