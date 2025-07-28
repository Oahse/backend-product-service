from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import List, Dict, Any
from datetime import date, timedelta

from models.visitors import VisitorEvents  # import your ORM model
from schemas.visitors import VisitorEventsSchema

class VisitorEventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_growth_result_simple(
        self,
        current_data: Dict[str, int],
        previous_data: Dict[str, int]
    ) -> Dict[str, Any]:
        total_visitors = sum(current_data.values())
        total_prev_visitors = sum(previous_data.values())

        if total_prev_visitors > 0:
            growth_percent = ((total_visitors - total_prev_visitors) / total_prev_visitors) * 100
        else:
            growth_percent = 100.0 if total_visitors > 0 else 0.0

        return {
            "total_visitors": total_visitors,
            "growth_percent": round(growth_percent, 2),
            "media": current_data
        }

    async def get_daily_visitors(self, day: date) -> List[Dict[str, Any]]:
        stmt = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date == day)
            .group_by(VisitorEvents.source)
        )
        res = await self.db.execute(stmt)
        return [dict(row._mapping) for row in res.all()]

    async def get_weekly_visitors(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        stmt = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date.between(start_date, end_date))
            .group_by(VisitorEvents.source)
        )
        res = await self.db.execute(stmt)
        return [dict(row._mapping) for row in res.all()]

    async def get_monthly_visitors(self, year: int, month: int) -> List[Dict[str, Any]]:
        stmt = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(
                extract('year', VisitorEvents.date) == year,
                extract('month', VisitorEvents.date) == month
            )
            .group_by(VisitorEvents.source)
        )
        res = await self.db.execute(stmt)
        return [dict(row._mapping) for row in res.all()]

    async def get_yearly_visitors(self, year: int) -> List[Dict[str, Any]]:
        stmt = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(extract('year', VisitorEvents.date) == year)
            .group_by(VisitorEvents.source)
        )
        res = await self.db.execute(stmt)
        return [dict(row._mapping) for row in res.all()]

    async def get_yearly_visitors_growth(self, year: int) -> Dict[str, Any]:
        stmt_current = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(extract('year', VisitorEvents.date) == year)
            .group_by(VisitorEvents.source)
        )
        stmt_previous = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(extract('year', VisitorEvents.date) == year - 1)
            .group_by(VisitorEvents.source)
        )

        current_res = await self.db.execute(stmt_current)
        previous_res = await self.db.execute(stmt_previous)

        current_data = {row._mapping["source"]: row._mapping["visitors"] for row in current_res.all()}
        previous_data = {row._mapping["source"]: row._mapping["visitors"] for row in previous_res.all()}

        return self._build_growth_result_simple(current_data, previous_data)

    async def get_monthly_visitors_growth(self, year: int, month: int) -> Dict[str, Any]:
        prev_month = month - 1 or 12
        prev_year = year if month > 1 else year - 1

        stmt_current = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(
                extract('year', VisitorEvents.date) == year,
                extract('month', VisitorEvents.date) == month
            )
            .group_by(VisitorEvents.source)
        )
        stmt_previous = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(
                extract('year', VisitorEvents.date) == prev_year,
                extract('month', VisitorEvents.date) == prev_month
            )
            .group_by(VisitorEvents.source)
        )

        current_res = await self.db.execute(stmt_current)
        previous_res = await self.db.execute(stmt_previous)

        current_data = {row._mapping["source"]: row._mapping["visitors"] for row in current_res.all()}
        previous_data = {row._mapping["source"]: row._mapping["visitors"] for row in previous_res.all()}

        return self._build_growth_result_simple(current_data, previous_data)

    async def get_weekly_visitors_growth(self, current_week_start: date) -> Dict[str, Any]:
        previous_week_start = current_week_start - timedelta(days=7)
        current_week_end = current_week_start + timedelta(days=6)
        previous_week_end = current_week_start - timedelta(days=1)

        stmt_current = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date.between(current_week_start, current_week_end))
            .group_by(VisitorEvents.source)
        )
        stmt_previous = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date.between(previous_week_start, previous_week_end))
            .group_by(VisitorEvents.source)
        )

        current_res = await self.db.execute(stmt_current)
        previous_res = await self.db.execute(stmt_previous)

        current_data = {row._mapping["source"]: row._mapping["visitors"] for row in current_res.all()}
        previous_data = {row._mapping["source"]: row._mapping["visitors"] for row in previous_res.all()}

        return self._build_growth_result_simple(current_data, previous_data)

    async def get_daily_visitors_growth(self, current_day: date) -> Dict[str, Any]:
        previous_day = current_day - timedelta(days=1)

        stmt = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date == current_day)
            .group_by(VisitorEvents.source)
        )
        stmt_prev = (
            select(
                VisitorEvents.source,
                func.sum(VisitorEvents.visitors).label("visitors")
            )
            .where(VisitorEvents.date == previous_day)
            .group_by(VisitorEvents.source)
        )

        current_res = await self.db.execute(stmt)
        previous_res = await self.db.execute(stmt_prev)

        current_data = {row._mapping["source"]: row._mapping["visitors"] for row in current_res.all()}
        previous_data = {row._mapping["source"]: row._mapping["visitors"] for row in previous_res.all()}

        return self._build_growth_result_simple(current_data, previous_data)
    
    async def add_or_update(
        self,
        data: VisitorEventsSchema,
        increment: bool = True
    ) -> VisitorEventsSchema:
        """
        Add or update a VisitorEvents record and return it as VisitorEventsSchema.

        Args:
            data (VisitorEventsSchema): validated input data
            increment (bool): if True, increment existing visitors count,
                              else overwrite it.

        Returns:
            VisitorEventsSchema: The added or updated record.
        """
        stmt = select(VisitorEvents).where(
            VisitorEvents.source == data.source,
            VisitorEvents.date == data.date
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            if increment:
                record.visitors += data.visitors
            else:
                record.visitors = data.visitors
        else:
            record = VisitorEvents(
                source=data.source,
                date=data.date,
                visitors=data.visitors
            )
            self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)  # Refresh to get DB state after commit

        return VisitorEventsSchema.from_orm(record)