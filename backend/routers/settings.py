"""
系统设置 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from services.database import get_db, SystemConfig

router = APIRouter()


class SaveSettingsRequest(BaseModel):
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_user_id: str = ""
    bailian_api_key: str = ""
    bailian_api_url: str = ""
    auto_monitor: bool = True
    alert_threshold: str = "medium"
    monitor_interval: int = 30
    ai_prompt: str = ""


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
async def get_settings_config(db: Session = Depends(get_db)):
    """获取系统设置配置"""
    return {
        "feishu_app_id": get_config_value(db, "feishu_app_id", ""),
        "feishu_app_secret": get_config_value(db, "feishu_app_secret", ""),
        "feishu_user_id": get_config_value(db, "feishu_user_id", ""),
        "bailian_api_key": get_config_value(db, "bailian_api_key", ""),
        "bailian_api_url": get_config_value(db, "bailian_api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
        "auto_monitor": get_config_value(db, "auto_monitor", "true") == "true",
        "alert_threshold": get_config_value(db, "alert_threshold", "medium"),
        "monitor_interval": get_config_value(db, "monitor_interval", "30"),
        "ai_prompt": get_config_value(db, "ai_prompt", ""),
    }


@router.post("/save-config")
async def save_settings_config(data: SaveSettingsRequest, db: Session = Depends(get_db)):
    """保存系统设置配置"""
    set_config_value(db, "feishu_app_id", data.feishu_app_id)
    set_config_value(db, "feishu_app_secret", data.feishu_app_secret)
    set_config_value(db, "feishu_user_id", data.feishu_user_id)
    set_config_value(db, "bailian_api_key", data.bailian_api_key)
    set_config_value(db, "bailian_api_url", data.bailian_api_url)
    set_config_value(db, "auto_monitor", "true" if data.auto_monitor else "false")
    set_config_value(db, "alert_threshold", data.alert_threshold)
    set_config_value(db, "monitor_interval", str(data.monitor_interval))
    if data.ai_prompt:
        set_config_value(db, "ai_prompt", data.ai_prompt)

    return {"success": True, "message": "配置已保存"}
