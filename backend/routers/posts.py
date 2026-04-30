"""
帖子管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database import get_db, WeiboPost, Comment

router = APIRouter()


@router.get("")
async def get_posts(star_id: int = None, db: Session = Depends(get_db)):
    """获取帖子列表"""
    query = db.query(WeiboPost)
    if star_id:
        query = query.filter(WeiboPost.star_id == star_id)

    posts = query.order_by(WeiboPost.created_at.desc()).limit(100).all()

    return [
        {
            "id": p.id,
            "star_id": p.star_id,
            "content": p.content,
            "sentiment": p.sentiment,
            "sentiment_score": p.sentiment_score,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "reposts_count": p.reposts_count,
            "source": p.source,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else None,
        }
        for p in posts
    ]


@router.get("/{id}")
async def get_post_detail(id: int, db: Session = Depends(get_db)):
    """获取帖子详情"""
    post = db.query(WeiboPost).filter(WeiboPost.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    return {
        "id": post.id,
        "star_id": post.star_id,
        "content": post.content,
        "sentiment": post.sentiment,
        "sentiment_score": post.sentiment_score,
        "likes_count": post.likes_count,
        "comments_count": post.comments_count,
        "reposts_count": post.reposts_count,
        "source": post.source,
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M") if post.created_at else None,
    }


@router.get("/{id}/comments")
async def get_post_comments(
    id: int,
    sentiment: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取帖子的评论列表"""
    # 检查帖子是否存在
    post = db.query(WeiboPost).filter(WeiboPost.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    query = db.query(Comment).filter(Comment.post_id == id)

    # 按情感过滤
    if sentiment:
        query = query.filter(Comment.sentiment == sentiment)

    comments = query.order_by(Comment.created_at.desc()).limit(limit).all()

    return {
        "post_id": id,
        "post_content": post.content,
        "total_comments": len(comments),
        "comments": [
            {
                "id": c.id,
                "user_name": c.user_name,
                "content": c.content,
                "likes_count": c.likes_count,
                "sentiment": c.sentiment,
                "sentiment_score": c.sentiment_score,
                "publish_time": c.publish_time,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else None,
            }
            for c in comments
        ]
    }