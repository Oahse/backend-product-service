from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db  # Your async session dependency
from services.kpis import KPIService, date
import json

router = APIRouter()

@router.websocket("/ws/kpis")
async def kpis_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    service = KPIService(db)

    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            action = request.get("action")
            payload = {}

            if action == "daily":
                start_date = request.get("start_date")
                end_date = request.get("end_date")

                if start_date:
                    start_date = date.fromisoformat(start_date)
                if end_date:
                    end_date = date.fromisoformat(end_date)

                results = await service.get_daily_kpis(start_date, end_date)
                payload = [r.to_dict() for r in results]

            elif action == "weekly":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"success": False, "error": "Missing 'year' parameter"}))
                    continue
                results = await service.get_weekly_kpis(year)
                payload = results

            elif action == "monthly":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"success": False, "error": "Missing 'year' parameter"}))
                    continue
                results = await service.get_monthly_kpis(year)
                payload = results

            elif action == "yearly":
                results = await service.get_yearly_kpis()
                payload = results

            elif action == "monthly_revenue":
                year = request.get("year")
                if not year:
                    await websocket.send_text(json.dumps({"success": False, "error": "Missing 'year' parameter"}))
                    continue
                results = await service.get_monthly_revenue_order_by_year(int(year))
                payload = results

            else:
                payload = {"error": "Unknown action"}

            await websocket.send_text(json.dumps({"success": True, "action": action, "data": payload}))

    except WebSocketDisconnect:
        print("Websocket disconnected")
