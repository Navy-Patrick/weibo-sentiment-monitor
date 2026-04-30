"""
关键词云 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.database import get_db, Keyword

router = APIRouter()


@router.get("/cloud")
async def get_keyword_cloud(
    star_id: int = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
):
    """获取关键词云数据"""
    keywords = db.query(Keyword).order_by(Keyword.count.desc()).limit(100).all()

    return [
        {
            "word": k.word,
            "count": k.count,
            "sentiment": k.sentiment,
        }
        for k in keywords
    ]