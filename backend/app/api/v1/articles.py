"""Articles API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession
from app.models.article import Article as ArticleModel
from app.models.citation import Citation as CitationModel
from app.schemas.article import Article, ArticleCreate, ArticleUpdate, ArticleWithStats, ArticleStats
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[Article])
async def list_articles(
    db: DatabaseSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    volume_number: int | None = None,
    issue_number: int | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[Article]:
    """List articles with filters and pagination."""
    query = select(ArticleModel)

    if status_filter:
        query = query.where(ArticleModel.status == status_filter)
    if volume_number:
        query = query.where(ArticleModel.volume_number == volume_number)
    if issue_number:
        query = query.where(ArticleModel.issue_number == issue_number)

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    articles = result.scalars().all()

    return PaginatedResponse(
        items=[Article.model_validate(article) for article in articles],
        total=total or 0,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page if total else 0,
    )


@router.post("", response_model=Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_in: ArticleCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> Article:
    """Create new article."""
    article = ArticleModel(**article_in.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return Article.model_validate(article)


@router.get("/{article_id}", response_model=ArticleWithStats)
async def get_article(
    article_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> ArticleWithStats:
    """Get article with citation statistics."""
    result = await db.execute(select(ArticleModel).where(ArticleModel.id == article_id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Get citation stats
    citations_result = await db.execute(
        select(CitationModel).where(CitationModel.article_id == article_id)
    )
    citations = citations_result.scalars().all()

    stats = ArticleStats(
        total_citations=len(citations),
        sp_completed=sum(1 for c in citations if c.sp_status == "completed"),
        r1_completed=sum(1 for c in citations if c.r1_status == "completed"),
        r2_completed=sum(1 for c in citations if c.r2_status == "completed"),
        requires_manual_review=sum(1 for c in citations if c.requires_manual_review),
        format_valid=sum(1 for c in citations if c.format_valid),
        support_valid=sum(1 for c in citations if c.support_valid),
        quote_valid=sum(1 for c in citations if c.quote_valid),
    )

    return ArticleWithStats(
        **Article.model_validate(article).model_dump(),
        citation_stats=stats
    )


@router.patch("/{article_id}", response_model=Article)
async def update_article(
    article_id: uuid.UUID,
    article_update: ArticleUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> Article:
    """Update article."""
    result = await db.execute(select(ArticleModel).where(ArticleModel.id == article_id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    update_data = article_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)
    return Article.model_validate(article)
