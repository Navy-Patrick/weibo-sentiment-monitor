"""
微博舆情监控系统 - FastAPI 后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dashboard, stars, sentiment, keywords, trends, collection, posts, settings, feishu
from services.scheduler import start_scheduler

app = FastAPI(
    title="微博舆情监控系统",
    description="监控明星微博舆情，进行情感分析",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(stars.router, prefix="/api/stars", tags=["明星管理"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["情感分析"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["关键词"])
app.include_router(trends.router, prefix="/api/trends", tags=["舆情趋势"])
app.include_router(collection.router, prefix="/api/collection", tags=["数据采集"])
app.include_router(posts.router, prefix="/api/posts", tags=["帖子管理"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])
app.include_router(feishu.router, prefix="/api/feishu", tags=["飞书推送"])

@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库和调度器"""
    from services.database import init_db
    await init_db()
    start_scheduler()

@app.get("/")
async def root():
    return {"message": "微博舆情监控系统 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}