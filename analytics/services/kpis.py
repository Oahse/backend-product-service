from sqlalchemy import func, extract, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from datetime import date
from models.kpis import DailyKPIs
from schemas.kpis import DailyKPIsSchema

from core.config import settings
from core.utils.kafka import KafkaProducer, send_kafka_message, is_kafka_available
from datetime import datetime,date


kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
                                topic=str(settings.KAFKA_TOPIC))

class KPIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_kpis(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[DailyKPIsSchema]:
        stmt = select(DailyKPIs)
        if start_date:
            stmt = stmt.where(DailyKPIs.date >= start_date)
        if end_date:
            stmt = stmt.where(DailyKPIs.date <= end_date)

        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return records

    async def get_weekly_kpis(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        # We approximate start of week by truncating date to Monday using date_trunc for PostgreSQL
        # Adjust based on your DB if not Postgres (for others, you might need raw SQL or custom func)
        week_start = func.date_trunc('week', DailyKPIs.date).label('week_start')

        stmt = (
            select(
                week_start,
                func.sum(DailyKPIs.total_orders).label('total_orders'),
                func.sum(DailyKPIs.total_revenue).label('total_revenue'),
                func.sum(DailyKPIs.total_customers).label('total_customers'),
                func.sum(DailyKPIs.total_earnings).label('total_earnings'),
            )
            .group_by(week_start)
            .order_by(week_start)
        )

        if year:
            stmt = stmt.where(extract('year', DailyKPIs.date) == year)

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "week_start": row.week_start.date(),
                "total_orders": row.total_orders,
                "total_revenue": row.total_revenue,
                "total_customers": row.total_customers,
                "total_earnings": row.total_earnings,
            }
            for row in rows
        ]

    async def get_monthly_kpis(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        month_start = func.date_trunc('month', DailyKPIs.date).label('month_start')

        stmt = (
            select(
                month_start,
                func.sum(DailyKPIs.total_orders).label('total_orders'),
                func.sum(DailyKPIs.total_revenue).label('total_revenue'),
                func.sum(DailyKPIs.total_customers).label('total_customers'),
                func.sum(DailyKPIs.total_earnings).label('total_earnings'),
            )
            .group_by(month_start)
            .order_by(month_start)
        )

        if year:
            stmt = stmt.where(extract('year', DailyKPIs.date) == year)

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "month_start": row.month_start.date(),
                "total_orders": row.total_orders,
                "total_revenue": row.total_revenue,
                "total_customers": row.total_customers,
                "total_earnings": row.total_earnings,
            }
            for row in rows
        ]

    async def get_yearly_kpis(self) -> List[Dict[str, Any]]:
        year_start = func.date_trunc('year', DailyKPIs.date).label('year_start')

        stmt = (
            select(
                year_start,
                func.sum(DailyKPIs.total_orders).label('total_orders'),
                func.sum(DailyKPIs.total_revenue).label('total_revenue'),
                func.sum(DailyKPIs.total_customers).label('total_customers'),
                func.sum(DailyKPIs.total_earnings).label('total_earnings'),
            )
            .group_by(year_start)
            .order_by(year_start)
        )

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "year_start": row.year_start.date(),
                "total_orders": row.total_orders,
                "total_revenue": row.total_revenue,
                "total_customers": row.total_customers,
                "total_earnings": row.total_earnings,
            }
            for row in rows
        ]

    async def get_monthly_revenue_order_by_year(self, year: int) -> Dict[str, Any]:
        # Get last two months for growth comparison
        month_start = func.date_trunc('month', DailyKPIs.date).label('month_start')
        stmt = (
            select(
                month_start,
                func.sum(DailyKPIs.total_orders).label('total_orders'),
                func.sum(DailyKPIs.total_revenue).label('total_revenue')
            )
            .where(extract('year', DailyKPIs.date) == year)
            .group_by(month_start)
            .order_by(month_start.desc())
            .limit(2)
        )

        result = await self.db.execute(stmt)
        growth_rows = result.all()

        current_month = growth_rows[0] if len(growth_rows) > 0 else None
        previous_month = growth_rows[1] if len(growth_rows) > 1 else None

        revenue_growth = 0.0
        order_growth = 0.0

        if previous_month and previous_month.total_revenue:
            revenue_growth = (
                (current_month.total_revenue - previous_month.total_revenue)
                / previous_month.total_revenue
            ) * 100

        if previous_month and previous_month.total_orders:
            order_growth = (
                (current_month.total_orders - previous_month.total_orders)
                / previous_month.total_orders
            ) * 100

        # Now fetch all months' data for the full year
        month_num = func.extract('month', DailyKPIs.date).label('month')

        stmt_all_months = (
            select(
                month_num,
                func.sum(DailyKPIs.total_orders).label('total_orders'),
                func.sum(DailyKPIs.total_revenue).label('total_revenue')
            )
            .where(extract('year', DailyKPIs.date) == year)
            .group_by(month_num)
            .order_by(month_num)
        )

        all_months_res = await self.db.execute(stmt_all_months)
        all_months = all_months_res.all()

        # Map month to data for easy lookup
        raw_data = {int(row.month): {"total_orders": row.total_orders, "total_revenue": row.total_revenue} for row in all_months}

        monthly_data = []
        for month in range(1, 13):
            first_day = date(year, month, 1)
            monthly_data.append({
                "month": first_day.strftime("%B"),
                "month_number": month,
                "total_orders": raw_data.get(month, {}).get("total_orders", 0),
                "total_revenue": raw_data.get(month, {}).get("total_revenue", 0.0),
            })

        return {
            "current_month_start": current_month.month_start.date() if current_month else None,
            "revenue": current_month.total_revenue if current_month else 0.0,
            "orders": current_month.total_orders if current_month else 0,
            "revenue_growth_percent": round(revenue_growth, 2),
            "order_growth_percent": round(order_growth, 2),
            "monthly_data": monthly_data,
        }
    
    async def add_or_update(self, kpi_data: DailyKPIsSchema) -> DailyKPIsSchema:
        # Try to get existing record by date
        stmt = select(DailyKPIs).where(DailyKPIs.date == kpi_data.date)
        result = await self.db.execute(stmt)
        existing_kpi = result.scalar_one_or_none()

        if existing_kpi:
            # Update existing record fields
            existing_kpi.total_orders = kpi_data.total_orders
            existing_kpi.total_revenue = kpi_data.total_revenue
            existing_kpi.total_customers = kpi_data.total_customers
            existing_kpi.total_earnings = kpi_data.total_earnings
            # No need to add it again, it's managed by session
            await self.db.commit()
            await self.db.refresh(existing_kpi)
            return DailyKPIsSchema.from_orm(existing_kpi)

        # Else create new record
        new_kpi = DailyKPIs(
            date=kpi_data.date,
            total_orders=kpi_data.total_orders,
            total_revenue=kpi_data.total_revenue,
            total_customers=kpi_data.total_customers,
            total_earnings=kpi_data.total_earnings,
        )
        self.db.add(new_kpi)
        await self.db.commit()
        await self.db.refresh(new_kpi)
        return DailyKPIsSchema.from_orm(new_kpi)
