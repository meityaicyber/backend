import uuid
from typing import Optional, List, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agency import Agency
from app.schemas.agency import AgencyCreate, AgencyUpdate


async def get_agencies(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> Tuple[List[Agency], int]:
    """Get paginated list of agencies."""
    # Count total
    count_result = await db.execute(select(func.count(Agency.agency_id)))
    total = count_result.scalar() or 0

    # Fetch agencies
    result = await db.execute(
        select(Agency)
        .order_by(Agency.name)
        .offset(skip)
        .limit(limit)
    )
    agencies = result.scalars().all()

    return list(agencies), total


async def get_agency_by_id(db: AsyncSession, agency_id: uuid.UUID) -> Optional[Agency]:
    """Get a single agency by ID."""
    result = await db.execute(
        select(Agency).where(Agency.agency_id == agency_id)
    )
    return result.scalar_one_or_none()


async def create_agency(db: AsyncSession, agency_in: AgencyCreate) -> Agency:
    """Create a new agency."""
    # Check existing
    existing = await db.execute(
        select(Agency).where(Agency.name == agency_in.name)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Agency with this name already exists")

    agency = Agency(
        name=agency_in.name,
        description=agency_in.description
    )
    db.add(agency)
    await db.flush()
    return agency


async def update_agency(
    db: AsyncSession, agency_id: uuid.UUID, agency_in: AgencyUpdate
) -> Optional[Agency]:
    """Update an existing agency."""
    agency = await get_agency_by_id(db, agency_id)
    if not agency:
        return None

    if agency_in.name is not None:
        # Check uniqueness
        existing = await db.execute(
            select(Agency).where(Agency.name == agency_in.name, Agency.agency_id != agency_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Agency with this name already exists")
        agency.name = agency_in.name

    if agency_in.description is not None:
        agency.description = agency_in.description

    await db.flush()
    return agency


async def delete_agency(db: AsyncSession, agency_id: uuid.UUID) -> bool:
    """Delete an agency."""
    agency = await get_agency_by_id(db, agency_id)
    if not agency:
        return False
    
    await db.execute(delete(Agency).where(Agency.agency_id == agency_id))
    await db.flush()
    return True
