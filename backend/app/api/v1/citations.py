"""Citations API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession
from app.models.citation import Citation as CitationModel
from app.schemas.citation import Citation, CitationCreate, CitationUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[Citation])
async def list_citations(
    db: DatabaseSession,
    current_user: CurrentUser,
    article_id: uuid.UUID | None = None,
    requires_manual_review: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[Citation]:
    """List citations with filters."""
    query = select(CitationModel)

    if article_id:
        query = query.where(CitationModel.article_id == article_id)
    if requires_manual_review is not None:
        query = query.where(CitationModel.requires_manual_review == requires_manual_review)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    citations = result.scalars().all()

    return PaginatedResponse(
        items=[Citation.model_validate(citation) for citation in citations],
        total=total or 0,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page if total else 0,
    )


@router.post("", response_model=Citation, status_code=status.HTTP_201_CREATED)
async def create_citation(
    citation_in: CitationCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> Citation:
    """Create new citation."""
    citation = CitationModel(**citation_in.model_dump())
    db.add(citation)
    await db.commit()
    await db.refresh(citation)
    return Citation.model_validate(citation)


@router.get("/{citation_id}", response_model=Citation)
async def get_citation(
    citation_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> Citation:
    """Get citation details."""
    result = await db.execute(select(CitationModel).where(CitationModel.id == citation_id))
    citation = result.scalar_one_or_none()

    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")

    return Citation.model_validate(citation)


@router.patch("/{citation_id}", response_model=Citation)
async def update_citation(
    citation_id: uuid.UUID,
    citation_update: CitationUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> Citation:
    """Update citation."""
    result = await db.execute(select(CitationModel).where(CitationModel.id == citation_id))
    citation = result.scalar_one_or_none()

    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")

    update_data = citation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(citation, field, value)

    await db.commit()
    await db.refresh(citation)
    return Citation.model_validate(citation)
