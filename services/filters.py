from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Lecture

async def get_lectures(
    session: AsyncSession,
    direction: str,
    course: int,
    subject: str,
    material_type: str,
    start: datetime,
    end: datetime
) -> List[Lecture]:
    stmt = (
        select(Lecture)
        .where(
            Lecture.direction == direction,
            Lecture.course == course,
            Lecture.subject == subject,
            Lecture.material_type == material_type,
            Lecture.date.between(start.date(), end.date())
        )
        .order_by(Lecture.date.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()