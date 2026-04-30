"""
仪表盘 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.database import get_db, Star, WeiboPost, HotTopic, SentimentRecord, Comment
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计数据"""
    stars = db.query(Star).filter(Star.status == "active").count()
    posts = db.query(WeiboPost).all()
    comments_count = db.query(Comment).count()

    positive_count = sum(1 for p in posts if p.sentiment == "positive")
    neutral_count = sum(1 for p in posts if p.sentiment == "neutral")
    negative_count = sum(1 for p in posts if p.sentiment == "negative")

    # 计算总互动量
    total_likes = sum(p.likes_count or 0 for p in posts)
    total_comments = sum(p.comments_count or 0 for p in posts)
    total_reposts = sum(p.reposts_count or 0 for p in posts)

    return {
        "star_count": stars,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "total_posts": len(posts),
        "total_comments": comments_count,
        "total_likes": total_likes,
        "total_interactions": total_likes + total_comments + total_reposts,
    }


@router.get("/hot-topics")
async def get_hot_topics(db: Session = Depends(get_db)):
    """获取近期热门话题 - 基于评论数排序"""
    # 获取评论数最多的帖子作为热门话题
    posts = db.query(WeiboPost).order_by(WeiboPost.comments_count.desc()).limit(10).all()

    topics = []
    for p in posts:
        # 获取明星名称
        star = db.query(Star).filter(Star.id == p.star_id).first()
        star_name = star.name if star else "未知"

        topics.append({
            "id": p.id,
            "title": p.content[:50] + "..." if len(p.content or "") > 50 else p.content or "",
            "star_name": star_name,
            "sentiment": p.sentiment or "neutral",
            "hot_value": p.comments_count or 0,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "未知时间",
        })

    return topics


@router.get("/sentiment-trend")
async def get_sentiment_trend(db: Session = Depends(get_db)):
    """获取情感趋势数据 - 基于评论的采集时间"""
    from sqlalchemy import func

    # 获取最近7天的评论，按日期分组统计情感
    today = datetime.now().date()
    trend_data = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        # 统计该日期的评论情感分布
        comments = db.query(Comment).filter(
            func.date(Comment.created_at) == date
        ).all()

        positive = sum(1 for c in comments if c.sentiment == "positive")
        negative = sum(1 for c in comments if c.sentiment == "negative")
        neutral = len(comments) - positive - negative

        trend_data.append({
            "date": date_str,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
        })

    return trend_data