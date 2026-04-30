"""
明星管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from services.database import get_db, Star, WeiboPost, Keyword, SentimentRecord
from datetime import datetime, timedelta
import random

router = APIRouter()


class StarCreate(BaseModel):
    name: str
    weibo_id: str
    avatar_url: str = ""


class PostImport(BaseModel):
    content: str
    sentiment: str = "neutral"
    sentiment_score: float = 0.5
    likes_count: int = 0
    comments_count: int = 0
    reposts_count: int = 0
    source: str = "weibo"


class PostsBatchImport(BaseModel):
    star_id: int
    posts: list[PostImport]


@router.get("")
async def get_stars(keyword: str = None, db: Session = Depends(get_db)):
    """获取明星列表"""
    query = db.query(Star)
    if keyword:
        query = query.filter(Star.name.contains(keyword))

    stars = query.all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "avatar_url": s.avatar_url or "https://via.placeholder.com/50",
            "weibo_id": s.weibo_id,
            "fans_count": s.fans_count,
            "sentiment_score": s.sentiment_score,
            "status": s.status,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for s in stars
    ]


@router.post("")
async def add_star(data: StarCreate, db: Session = Depends(get_db)):
    """添加明星"""
    # 检查是否已存在
    existing = db.query(Star).filter(Star.weibo_id == data.weibo_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该明星已存在")

    star = Star(
        name=data.name,
        weibo_id=data.weibo_id,
        avatar_url=data.avatar_url,
        fans_count=0,
        sentiment_score=0.5,
        status="active",
    )
    db.add(star)
    db.commit()
    db.refresh(star)
    return {"id": star.id, "message": "添加成功"}


@router.delete("/{id}")
async def delete_star(id: int, db: Session = Depends(get_db)):
    """删除明星"""
    star = db.query(Star).filter(Star.id == id).first()
    if not star:
        raise HTTPException(status_code=404, detail="明星不存在")

    db.delete(star)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{id}")
async def get_star_detail(id: int, db: Session = Depends(get_db)):
    """获取明星详情"""
    star = db.query(Star).filter(Star.id == id).first()
    if not star:
        raise HTTPException(status_code=404, detail="明星不存在")

    posts = db.query(WeiboPost).filter(WeiboPost.star_id == id).all()
    positive = sum(1 for p in posts if p.sentiment == "positive")
    neutral = sum(1 for p in posts if p.sentiment == "neutral")
    negative = sum(1 for p in posts if p.sentiment == "negative")

    keywords = db.query(Keyword).limit(20).all()

    return {
        "id": star.id,
        "name": star.name,
        "avatar_url": star.avatar_url or "https://via.placeholder.com/50",
        "weibo_id": star.weibo_id,
        "fans_count": star.fans_count,
        "sentiment_score": star.sentiment_score,
        "status": star.status,
        "total_posts": len(posts),
        "positive_posts": positive,
        "neutral_posts": neutral,
        "negative_posts": negative,
        "keywords": [{"word": k.word, "count": k.count, "sentiment": k.sentiment} for k in keywords],
        "created_at": star.created_at.strftime("%Y-%m-%d %H:%M"),
    }


@router.get("/{id}/sentiment-history")
async def get_star_sentiment_history(id: int, db: Session = Depends(get_db)):
    """获取明星情感历史"""
    records = db.query(SentimentRecord).filter(SentimentRecord.star_id == id).order_by(SentimentRecord.date.desc()).limit(30).all()

    if not records:
        # 如果没有记录，生成模拟数据
        today = datetime.utcnow()
        result = []
        for i in range(30):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            score = 0.5 + (random.random() - 0.5) * 0.3
            result.append({"date": date, "score": score})
        return result

    return [{"date": r.date, "score": r.avg_score} for r in records]


@router.post("/{id}/posts/batch")
async def batch_import_posts(id: int, data: PostsBatchImport, db: Session = Depends(get_db)):
    """批量导入帖子"""
    star = db.query(Star).filter(Star.id == id).first()
    if not star:
        raise HTTPException(status_code=404, detail="明星不存在")

    imported_count = 0
    for post_data in data.posts:
        post = WeiboPost(
            star_id=id,
            content=post_data.content,
            sentiment=post_data.sentiment,
            sentiment_score=post_data.sentiment_score,
            likes_count=post_data.likes_count,
            comments_count=post_data.comments_count,
            reposts_count=post_data.reposts_count,
            source=post_data.source,
        )
        db.add(post)
        imported_count += 1

    db.commit()
    return {"message": "批量导入成功", "imported_count": imported_count}


@router.get("/{id}/posts")
async def get_star_posts(id: int, db: Session = Depends(get_db)):
    """获取明星微博列表"""
    posts = db.query(WeiboPost).filter(WeiboPost.star_id == id).order_by(WeiboPost.created_at.desc()).limit(50).all()
    return [
        {
            "id": p.id,
            "content": p.content,
            "sentiment": p.sentiment,
            "sentiment_score": p.sentiment_score,
            "reposts_count": p.reposts_count,
            "comments_count": p.comments_count,
            "likes_count": p.likes_count,
            "source": p.source,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for p in posts
    ]