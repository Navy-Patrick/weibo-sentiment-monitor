"""路由模块"""
from .dashboard import router as dashboard_router
from .stars import router as stars_router
from .sentiment import router as sentiment_router
from .keywords import router as keywords_router
from .trends import router as trends_router

# 导出所有路由器，方便在 main.py 中导入
__all__ = ["dashboard_router", "stars_router", "sentiment_router", "keywords_router", "trends_router"]