from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.visitors import VisitorEventService  # adjust import path as needed
from datetime import date
import json

router = APIRouter()

@router.websocket("/ws/visitor-events")
async def visitor_events_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    service = VisitorEventService(db)

    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            action = request.get("action")
            response_data = None

            if action == "daily":
                day_str = request.get("date")
                if not day_str:
                    await websocket.send_text(json.dumps({"error": "Missing 'date' parameter"}))
                    continue
                day = date.fromisoformat(day_str)
                response_data = await service.get_daily_visitors(day)

            elif action == "weekly":
                start_str = request.get("start_date")
                end_str = request.get("end_date")
                if not start_str or not end_str:
                    await websocket.send_text(json.dumps({"error": "Missing 'start_date' or 'end_date' parameter"}))
                    continue
                start_date = date.fromisoformat(start_str)
                end_date = date.fromisoformat(end_str)
                response_data = await service.get_weekly_visitors(start_date, end_date)

            elif action == "monthly":
                year = request.get("year")
                month = request.get("month")
                if not year or not month:
                    await websocket.send_text(json.dumps({"error": "Missing 'year' or 'month' parameter"}))
                    continue
                response_data = await service.get_monthly_visitors(int(year), int(month))

            elif action == "yearly":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"error": "Missing 'year' parameter"}))
                    continue
                response_data = await service.get_yearly_visitors(int(year))

            elif action == "growth_daily":
                day_str = request.get("date")
                if not day_str:
                    await websocket.send_text(json.dumps({"error": "Missing 'date' parameter"}))
                    continue
                day = date.fromisoformat(day_str)
                response_data = await service.get_daily_visitors_growth(day)

            elif action == "growth_weekly":
                start_str = request.get("start_date")
                if not start_str:
                    await websocket.send_text(json.dumps({"error": "Missing 'start_date' parameter"}))
                    continue
                start_date = date.fromisoformat(start_str)
                response_data = await service.get_weekly_visitors_growth(start_date)

            elif action == "growth_monthly":
                year = request.get("year")
                month = request.get("month")
                if not year or not month:
                    await websocket.send_text(json.dumps({"error": "Missing 'year' or 'month' parameter"}))
                    continue
                response_data = await service.get_monthly_visitors_growth(int(year), int(month))

            elif action == "growth_yearly":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"error": "Missing 'year' parameter"}))
                    continue
                response_data = await service.get_yearly_visitors_growth(int(year))

            else:
                await websocket.send_text(json.dumps({"error": "Unknown action"}))
                continue

            await websocket.send_text(json.dumps({"action": action, "data": response_data}))

    except WebSocketDisconnect:
        print("WebSocket disconnected")
