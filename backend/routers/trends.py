"""
舆情趋势 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.database import get_db, HotTopic, SentimentRecord
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("")
async def get_trends(
    star_id: int = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
):
    """获取舆情趋势数据"""
    # 构建趋势数据
    trend = []
    today = datetime.utcnow()
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        hot_index = random.randint(5000, 10000)
        positive_ratio = random.uniform(0.5, 0.8)
        negative_ratio = random.uniform(0.1, 0.3)
        trend.append({
            "date": date,
            "hot_index": hot_index,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
        })

    # 构建热门事件
    hot_events = db.query(HotTopic).order_by(HotTopic.hot_value.desc()).limit(10).all()
    if not hot_events:
        hot_events = [
            {"id": 1, "title": "明星新剧热播", "star_name": "迪丽热巴", "sentiment": "positive", "hot_value": 9500, "created_at": "2026-04-29"},
            {"id": 2, "title": "时尚大片发布", "star_name": "杨幂", "sentiment": "positive", "hot_value": 8800, "created_at": "2026-04-28"},
            {"id": 3, "title": "新作品获得好评", "star_name": "赵丽颖", "sentiment": "positive", "hot_value": 7500, "created_at": "2026-04-27"},
        ]

    # 构建事件列表
    events = db.query(HotTopic).order_by(HotTopic.created_at.desc()).limit(20).all()

    return {
        "trend": trend,
        "hot_events": [
            {
                "id": e.id if hasattr(e, 'id') else i,
                "title": e.title if hasattr(e, 'title') else e["title"],
                "hot_value": e.hot_value if hasattr(e, 'hot_value') else e["hot_value"],
            }
            for i, e in enumerate(hot_events)
        ],
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "star_name": e.star_name,
                "sentiment": e.sentiment,
                "hot_value": e.hot_value,
                "created_at": e.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for e in events
        ] if events else [
            {"id": 1, "title": "明星新剧热播", "star_name": "迪丽热巴", "sentiment": "positive", "hot_value": 9500, "created_at": "2026-04-29"},
            {"id": 2, "title": "时尚大片发布", "star_name": "杨幂", "sentiment": "positive", "hot_value": 8800, "created_at": "2026-04-28"},
        ],
    }