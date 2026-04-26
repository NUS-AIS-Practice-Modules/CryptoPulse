from fastapi import APIRouter, HTTPException, Query
from src.services.sentiment_service import get_summary

router = APIRouter()


@router.get("/api/sentiment/summary")
async def sentiment_summary(
    crypto: str = Query(..., description="Ticker symbol, e.g. BTC"),
    period: str = Query("7d", description="Time period: 7d | 30d | 90d"),
):
    try:
        return get_summary(crypto, period)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation failure: {e}")
