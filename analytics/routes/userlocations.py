from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.userlocations import UserLocationStatsService  # Adjust import path
from datetime import date
import json

router = APIRouter()

@router.websocket("/ws/user-location-stats")
async def user_location_stats_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    service = UserLocationStatsService(db)

    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            action = request.get("action")

            if action == "daily":
                target_date_str = request.get("date")
                if not target_date_str:
                    await websocket.send_text(json.dumps({"success": False, "message": "Missing 'date' parameter"}))
                    continue
                target_date = date.fromisoformat(target_date_str)
                result = await service.get_daily_stats(target_date)

            elif action == "weekly":
                target_date_str = request.get("date")
                if not target_date_str:
                    await websocket.send_text(json.dumps({"success": False, "message": "Missing 'date' parameter"}))
                    continue
                target_date = date.fromisoformat(target_date_str)
                result = await service.get_weekly_stats(target_date)

            elif action == "monthly":
                year = request.get("year")
                month = request.get("month")
                if not year or not month:
                    await websocket.send_text(json.dumps({"success": False, "message": "Missing 'year' or 'month' parameter"}))
                    continue
                result = await service.get_monthly_stats(int(year), int(month))

            elif action == "yearly":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"success": False, "message": "Missing 'year' parameter"}))
                    continue
                result = await service.get_yearly_stats(int(year))

            elif action == "country_distribution":
                target_date_str = request.get("date")
                if not target_date_str:
                    await websocket.send_text(json.dumps({"success": False, "message": "Missing 'date' parameter"}))
                    continue
                target_date = date.fromisoformat(target_date_str)
                result = await service.get_country_percent_distribution(target_date)

            else:
                await websocket.send_text(json.dumps({"success": False, "message": "Unknown action"}))
                continue

            await websocket.send_text(json.dumps({"success": True, "action": action, "data": result}))

    except WebSocketDisconnect:
        print("WebSocket disconnected")
