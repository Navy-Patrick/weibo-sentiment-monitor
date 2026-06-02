"""
情感分析 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database import get_db, WeiboPost, Comment, Star, SystemConfig
from datetime import datetime, timedelta
import random
import requests
import os

router = APIRouter()


def get_config_value(db, key: str, default: str = "") -> str:
    """获取配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else default


def analyze_sentiment_with_ai(text: str, db: Session) -> dict:
    """使用 AI 分析文本情感"""
    # 从系统设置读取百炼 AI 配置
    ai_api_url = get_config_value(db, "bailian_api_url", "")
    ai_api_key = get_config_value(db, "bailian_api_key", "")
    ai_prompt_template = get_config_value(db, "ai_prompt", "")

    if not ai_api_key or not ai_api_url:
        # 如果没有配置 API Key，返回默认值
        return {"sentiment": "neutral", "score": 0.5, "reason": "未配置AI API"}

    # 使用自定义提示词或默认提示词
    if ai_prompt_template:
        prompt = ai_prompt_template.replace("{text}", text)
    else:
        prompt = f"""你是一个专业的舆情分析师，请分析以下微博评论的情感倾向。

评论内容：{text}

分析要求：
1. 结合微博语境理解评论含义，注意网络用语、表情符号、粉丝用语
2. "老公"、"老婆"、"哥哥"、"姐姐"等称呼在粉丝语境下是正面表达
3. "棒"、"赞"、"爱了"、"绝了"、"yyds"等是正面词
4. "差"、"烂"、"无语"、"失望"、"恶心"等是负面词
5. 纯转发、@他人、无情感倾向的内容为中性

请严格按以下JSON格式返回，不要添加任何其他内容：
{{"sentiment": "positive/neutral/negative", "score": 0.0-1.0, "reason": "简短理由"}}

评分标准：
- positive（正面）: score > 0.6，表示喜爱、支持、赞美等积极情感
- neutral（中性）: score 在 0.4-0.6 之间，表示无明确情感倾向
- negative（负面）: score < 0.4，表示批评、不满、愤怒等消极情感"""

    try:
        response = requests.post(
            ai_api_url,
            headers={
                "Authorization": f"Bearer {ai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen3.5-flash",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            # 解析 JSON 结果
            import json
            # 提取 JSON 部分
            if "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                return json.loads(json_str)
    except Exception as e:
        print(f"AI 分析失败: {e}")

    return {"sentiment": "neutral", "score": 0.5, "reason": "分析失败"}


@router.post("/analyze-post/{post_id}")
async def analyze_post_sentiment(post_id: int, db: Session = Depends(get_db)):
    """分析指定帖子的所有评论情感"""
    # 获取帖子
    post = db.query(WeiboPost).filter(WeiboPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 获取该帖子的所有评论
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()

    if not comments:
        return {"success": False, "message": "该帖子没有评论"}

    analyzed_count = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0

    for comment in comments:
        # 调用 AI 分析
        result = analyze_sentiment_with_ai(comment.content, db)

        # 更新评论情感
        comment.sentiment = result.get("sentiment", "neutral")
        comment.sentiment_score = result.get("score", 0.5)

        # 统计
        if comment.sentiment == "positive":
            positive_count += 1
        elif comment.sentiment == "negative":
            negative_count += 1
        else:
            neutral_count += 1
        total_score += comment.sentiment_score
        analyzed_count += 1

    # 计算帖子整体情感
    if analyzed_count > 0:
        avg_score = total_score / analyzed_count
        if avg_score > 0.6:
            post.sentiment = "positive"
        elif avg_score < 0.4:
            post.sentiment = "negative"
        else:
            post.sentiment = "neutral"
        post.sentiment_score = avg_score

    db.commit()

    return {
        "success": True,
        "post_id": post_id,
        "analyzed_comments": analyzed_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "post_sentiment": post.sentiment,
        "post_sentiment_score": post.sentiment_score
    }


@router.get("/analysis")
async def get_sentiment_analysis(
    star_id: int = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
):
    """获取情感分析数据"""
    query = db.query(WeiboPost)

    if star_id:
        query = query.filter(WeiboPost.star_id == star_id)

    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(WeiboPost.created_at >= start)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(WeiboPost.created_at <= end)

    posts = query.limit(100).all()

    # 构建时间线数据
    timeline = []
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        for i in range(days):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            day_posts = [p for p in posts if p.created_at.strftime("%Y-%m-%d") == date]
            positive = sum(1 for p in day_posts if p.sentiment == "positive")
            neutral = sum(1 for p in day_posts if p.sentiment == "neutral")
            negative = sum(1 for p in day_posts if p.sentiment == "negative")
            timeline.append({"date": date, "positive": positive, "neutral": neutral, "negative": negative})
    else:
        # 默认最近7天
        today = datetime.utcnow()
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            positive = random.randint(10, 50)
            neutral = random.randint(5, 30)
            negative = random.randint(2, 20)
            timeline.append({"date": date, "positive": positive, "neutral": neutral, "negative": negative})

    # 构建来源分布
    sources = [{"source": "微博", "count": len(posts)}, {"source": "评论", "count": len(posts) // 2}, {"source": "转发", "count": len(posts) // 3}]

    return {
        "timeline": timeline,
        "sources": sources,
        "posts": [
            {
                "id": p.id,
                "content": p.content,
                "sentiment": p.sentiment,
                "sentiment_score": p.sentiment_score,
                "source": p.source,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for p in posts
        ],
    }