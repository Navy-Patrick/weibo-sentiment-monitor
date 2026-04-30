"""
飞书推送 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.database import get_db, WeiboPost, Comment, Star, SystemConfig
import requests
import time
import json

router = APIRouter()


def get_config_value(db, key: str, default: str = "") -> str:
    """获取配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else default


def get_feishu_token(app_id: str, app_secret: str) -> str:
    """获取飞书 access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                return result.get("tenant_access_token", "")
    except Exception as e:
        print(f"获取飞书 token 失败: {e}")
    return ""


def send_feishu_message_to_user(token: str, user_id: str, content: str) -> bool:
    """发送消息给个人用户"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=user_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("code") == 0
    except Exception as e:
        print(f"发送飞书消息失败: {e}")
    return False


@router.post("/push-analysis")
async def push_analysis_to_feishu(db: Session = Depends(get_db)):
    """推送 AI 分析结果到飞书"""
    app_id = get_config_value(db, "feishu_app_id", "")
    app_secret = get_config_value(db, "feishu_app_secret", "")
    user_id = get_config_value(db, "feishu_user_id", "")

    if not app_id or not app_secret:
        return {"success": False, "message": "未配置飞书 App ID 或 App Secret"}

    if not user_id:
        return {"success": False, "message": "未配置飞书用户 ID"}

    # 获取 access_token
    token = get_feishu_token(app_id, app_secret)
    if not token:
        return {"success": False, "message": "获取飞书 token 失败"}

    # 获取已分析的帖子
    posts = db.query(WeiboPost).filter(WeiboPost.sentiment != None).all()

    if not posts:
        return {"success": False, "message": "没有已分析的帖子"}

    pushed_count = 0
    for post in posts[:5]:  # 每次最多推送5条
        # 获取明星名称
        star = db.query(Star).filter(Star.id == post.star_id).first()
        star_name = star.name if star else "未知"

        # 获取评论情感统计
        comments = db.query(Comment).filter(Comment.post_id == post.id).all()
        positive = sum(1 for c in comments if c.sentiment == "positive")
        negative = sum(1 for c in comments if c.sentiment == "negative")
        neutral = sum(1 for c in comments if c.sentiment == "neutral")
        total = len(comments)

        # 情感文本
        sentiment_text = {
            "positive": "正面",
            "negative": "负面",
            "neutral": "中性"
        }.get(post.sentiment, "未知")

        score_percent = (post.sentiment_score or 0.5) * 100

        # 构建消息内容
        content = f"""【舆情分析报告】

👤 明星：{star_name}

📝 帖子：
{post.content[:100]}{'...' if len(post.content) > 100 else ''}

📊 情感分析：
整体情感：{sentiment_text} ({score_percent:.0f}%)
评论统计：共 {total} 条
  ✅ 正面：{positive}
  ❌ 负面：{negative}
  ⚪ 中性：{neutral}"""

        if send_feishu_message_to_user(token, user_id, content):
            pushed_count += 1

    return {"success": True, "pushed_count": pushed_count}


@router.post("/test")
async def test_feishu_push(db: Session = Depends(get_db)):
    """测试飞书推送"""
    app_id = get_config_value(db, "feishu_app_id", "")
    app_secret = get_config_value(db, "feishu_app_secret", "")
    user_id = get_config_value(db, "feishu_user_id", "")

    if not app_id or not app_secret:
        return {"success": False, "message": "未配置飞书 App ID 或 App Secret"}

    if not user_id:
        return {"success": False, "message": "未配置飞书用户 ID"}

    token = get_feishu_token(app_id, app_secret)
    if not token:
        return {"success": False, "message": "获取飞书 token 失败"}

    content = "【测试消息】\n\n微博舆情监控系统已连接！推送功能正常工作。"

    if send_feishu_message_to_user(token, user_id, content):
        return {"success": True, "message": "测试消息已发送"}
    else:
        return {"success": False, "message": "发送失败，请检查配置或权限"}
