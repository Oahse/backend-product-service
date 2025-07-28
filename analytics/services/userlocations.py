from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.visitors import UserLocationStats  # adjust path if needed


class UserLocationStatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats_by_date(self, target_date: date) -> List[Dict[str, any]]:
        stmt = (
            select(
                UserLocationStats.country,
                UserLocationStats.state,
                func.sum(UserLocationStats.users).label("users")
            )
            .where(UserLocationStats.date == target_date)
            .group_by(UserLocationStats.country, UserLocationStats.state)
        )
        result = await self.db.execute(stmt)
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_stats_between_dates(self, start: date, end: date) -> List[Dict[str, any]]:
        stmt = (
            select(
                UserLocationStats.country,
                UserLocationStats.state,
                func.sum(UserLocationStats.users).label("users")
            )
            .where(and_(UserLocationStats.date >= start, UserLocationStats.date <= end))
            .group_by(UserLocationStats.country, UserLocationStats.state)
        )
        result = await self.db.execute(stmt)
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_daily_stats(self, current_day: date) -> Dict[str, any]:
        return {
            "date": current_day.isoformat(),
            "locations": await self.get_stats_by_date(current_day)
        }

    async def get_weekly_stats(self, current_day: date) -> Dict[str, any]:
        start_of_week = current_day - timedelta(days=current_day.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "locations": await self.get_stats_between_dates(start_of_week, end_of_week)
        }

    async def get_monthly_stats(self, year: int, month: int) -> Dict[str, any]:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        return {
            "month": start_date.strftime("%B"),
            "year": year,
            "locations": await self.get_stats_between_dates(start_date, end_date)
        }

    async def get_yearly_stats(self, year: int) -> Dict[str, any]:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return {
            "year": year,
            "locations": await self.get_stats_between_dates(start_date, end_date)
        }

    async def get_country_percent_distribution(self, target_date: date) -> Dict[str, float]:
        stmt = (
            select(
                UserLocationStats.country,
                func.sum(UserLocationStats.users).label("users")
            )
            .where(UserLocationStats.date == target_date)
            .group_by(UserLocationStats.country)
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        total = sum(row.users for row in rows)
        return {
            row.country: round((row.users / total) * 100, 2) if total > 0 else 0.0
            for row in rows
        }
