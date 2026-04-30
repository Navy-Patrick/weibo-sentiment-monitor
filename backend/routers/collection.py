"""
数据采集 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import get_db, Star, CollectionTask, SyncSessionLocal, SystemConfig
from services.crawler import start_async_collection, get_current_task, set_stop_flag

router = APIRouter()


class CollectionStartRequest(BaseModel):
    weibo_uid: str
    cookie: str = ""  # CDP 模式不需要 cookie，保留字段兼容前端
    posts_count: int = 100
    comments_per_post: int = 100


class CollectionStopRequest(BaseModel):
    pass


class SaveConfigRequest(BaseModel):
    ai_api_url: str = ""
    ai_api_key: str = ""
    posts_count: int = 100
    comments_per_post: int = 100


def get_config_value(db, key: str, default: str = "") -> str:
    """获取配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else default


def set_config_value(db, key: str, value: str):
    """设置配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        config.value = value
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    db.commit()


@router.get("/config")
async def get_collection_config(db: Session = Depends(get_db)):
    """获取采集配置和已采集的明星列表"""
    stars = db.query(Star).filter(Star.status == "active").all()

    # 从数据库读取保存的配置
    ai_api_url = get_config_value(db, "ai_api_url", "")
    ai_api_key = get_config_value(db, "ai_api_key", "")
    posts_count = int(get_config_value(db, "posts_count", "100"))
    comments_per_post = int(get_config_value(db, "comments_per_post", "100"))

    return {
        "stars": [
            {
                "id": s.id,
                "weibo_uid": s.weibo_id,
                "nickname": s.name,
                "fans_count": s.fans_count,
            }
            for s in stars
        ],
        "saved_config": {
            "ai_api_url": ai_api_url,
            "ai_api_key": ai_api_key,
            "posts_count": posts_count,
            "comments_per_post": comments_per_post,
        },
        "default_config": {
            "posts_count": posts_count,
            "comments_per_post": comments_per_post,
        }
    }


@router.post("/save-config")
async def save_collection_config(data: SaveConfigRequest, db: Session = Depends(get_db)):
    """保存采集配置"""
    set_config_value(db, "ai_api_url", data.ai_api_url)
    set_config_value(db, "ai_api_key", data.ai_api_key)
    set_config_value(db, "posts_count", str(data.posts_count))
    set_config_value(db, "comments_per_post", str(data.comments_per_post))

    return {"success": True, "message": "配置已保存"}


@router.get("/status")
async def get_collection_status(db: Session = Depends(get_db)):
    """获取当前采集状态"""
    current = get_current_task()

    # 从数据库获取最新的任务
    latest_task = db.query(CollectionTask).order_by(CollectionTask.id.desc()).first()

    result = None
    last_collection_time = None

    if latest_task:
        # 安全获取时间 - 优先用 completed_at，其次 started_at，最后 created_at
        time_to_use = latest_task.completed_at or latest_task.started_at or latest_task.created_at
        if time_to_use:
            last_collection_time = time_to_use.strftime("%Y-%m-%d %H:%M")

        if latest_task.status == "completed":
            star = db.query(Star).filter(Star.id == latest_task.star_id).first()
            result = {
                "success": True,
                "message": f"采集完成：{latest_task.posts_count} 条帖子，{latest_task.comments_count} 条评论",
                "star": {
                    "id": star.id if star else None,
                    "weibo_uid": latest_task.weibo_uid,
                    "nickname": star.name if star else "",
                    "fans_count": star.fans_count if star else 0,
                },
                "posts_count": latest_task.posts_count,
                "comments_count": latest_task.comments_count,
            }
        elif latest_task.status == "failed":
            result = {
                "success": False,
                "message": f"采集失败：{latest_task.error_message}",
            }
        elif latest_task.status == "stopped":
            result = {
                "success": False,
                "message": "采集已停止",
            }

    return {
        "is_running": current.get("is_running", False) if current else False,
        "last_collection": last_collection_time,
        "current_progress": {
            "posts_fetched": current.get("posts_fetched", 0) if current else 0,
            "comments_fetched": current.get("comments_fetched", 0) if current else 0,
            "current_post": current.get("current_post", "") if current else "",
        } if current else None,
        "result": result,
    }


@router.post("/start")
async def start_collection(data: CollectionStartRequest, db: Session = Depends(get_db)):
    """启动采集任务（异步执行）"""
    # 检查是否已有任务运行
    current = get_current_task()
    if current and current.get("is_running"):
        raise HTTPException(status_code=400, detail="已有采集任务在运行")

    # 检查明星是否已存在
    star = db.query(Star).filter(Star.weibo_id == data.weibo_uid).first()

    # 启动异步采集任务
    task_id = start_async_collection(
        weibo_uid=data.weibo_uid,
        posts_count=data.posts_count,
        comments_per_post=data.comments_per_post
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "采集任务已启动",
        "star_id": star.id if star else None,
    }


@router.post("/stop")
async def stop_collection(db: Session = Depends(get_db)):
    """停止采集任务"""
    current = get_current_task()
    if not current or not current.get("is_running"):
        return {"message": "当前没有运行的任务"}

    set_stop_flag(True)

    # 更新数据库任务状态
    latest_task = db.query(CollectionTask).order_by(CollectionTask.created_at.desc()).first()
    if latest_task and latest_task.status == "running":
        latest_task.status = "stopped"
        latest_task.completed_at = datetime.utcnow()
        db.commit()

    return {"message": "已标记停止采集"}


@router.get("/tasks")
async def get_collection_tasks(db: Session = Depends(get_db)):
    """获取采集任务历史"""
    tasks = db.query(CollectionTask).order_by(CollectionTask.created_at.desc()).limit(20).all()

    return [
        {
            "id": t.id,
            "star_id": t.star_id,
            "weibo_uid": t.weibo_uid,
            "status": t.status,
            "posts_count": t.posts_count,
            "comments_count": t.comments_count,
            "error_message": t.error_message,
            "started_at": t.started_at.strftime("%Y-%m-%d %H:%M") if t.started_at else None,
            "completed_at": t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else None,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for t in tasks
    ]