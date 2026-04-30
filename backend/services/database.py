"""
数据库模型和初始化
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 同步引擎（用于初始化）
sync_engine = create_engine(f"sqlite:///{DB_PATH}")
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class Star(Base):
    """明星表"""
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), default="")
    weibo_id = Column(String(100), unique=True, nullable=False)
    fans_count = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.5)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeiboPost(Base):
    """微博帖子表"""
    __tablename__ = "weibo_posts"

    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)  # 关联 stars.id
    content = Column(Text, nullable=False)
    sentiment = Column(String(20), default="neutral")
    sentiment_score = Column(Float, default=0.5)
    reposts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    source = Column(String(50), default="weibo")
    keywords = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class HotTopic(Base):
    """热门话题表"""
    __tablename__ = "hot_topics"

    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)
    star_name = Column(String(100))
    title = Column(String(500), nullable=False)
    sentiment = Column(String(20), default="neutral")
    hot_value = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Keyword(Base):
    """关键词表"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), unique=True, nullable=False)
    count = Column(Integer, default=0)
    sentiment = Column(String(20), default="neutral")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SentimentRecord(Base):
    """情感记录表"""
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)
    date = Column(String(20), nullable=False)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    avg_score = Column(Float, default=0.5)


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)  # 关联 weibo_posts.id
    weibo_comment_id = Column(String(100))  # 微博原始评论ID
    user_name = Column(String(100))
    user_id = Column(String(100))
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    sentiment = Column(String(20), default="neutral")
    sentiment_score = Column(Float, default=0.5)
    publish_time = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class CollectionTask(Base):
    """采集任务表"""
    __tablename__ = "collection_tasks"

    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)
    weibo_uid = Column(String(100))
    posts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending/running/completed/failed/stopped
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=sync_engine)

    # 创建默认数据
    db = SyncSessionLocal()
    try:
        # 检查是否已有明星数据
        if db.query(Star).count() == 0:
            # 添加示例明星
            sample_stars = [
                Star(name="迪丽热巴", weibo_id="dilireba", fans_count=80000000, sentiment_score=0.7),
                Star(name="杨幂", weibo_id="yangmi", fans_count=110000000, sentiment_score=0.6),
                Star(name="赵丽颖", weibo_id="zhao_liying", fans_count=90000000, sentiment_score=0.75),
                Star(name="王一博", weibo_id="wangyibo", fans_count=50000000, sentiment_score=0.65),
                Star(name="肖战", weibo_id="xiaozhan", fans_count=55000000, sentiment_score=0.55),
            ]
            db.add_all(sample_stars)

        # 检查是否已有微博数据
        if db.query(WeiboPost).count() == 0:
            # 添加示例微博数据
            sample_posts = [
                WeiboPost(star_id=1, content="今天又是美好的一天，感谢大家的支持！", sentiment="positive", sentiment_score=0.85, likes_count=50000),
                WeiboPost(star_id=1, content="新剧即将上线，希望大家喜欢", sentiment="positive", sentiment_score=0.72, likes_count=80000),
                WeiboPost(star_id=2, content="分享一些生活日常", sentiment="neutral", sentiment_score=0.5, likes_count=30000),
                WeiboPost(star_id=3, content="感谢粉丝们的陪伴，我们会继续努力", sentiment="positive", sentiment_score=0.78, likes_count=100000),
                WeiboPost(star_id=4, content="今天很累，但依然坚持", sentiment="neutral", sentiment_score=0.4, likes_count=45000),
                WeiboPost(star_id=5, content="新歌发布，期待大家的反馈", sentiment="neutral", sentiment_score=0.55, likes_count=60000),
            ]
            db.add_all(sample_posts)

        # 检查是否已有热门话题
        if db.query(HotTopic).count() == 0:
            sample_topics = [
                HotTopic(star_id=1, star_name="迪丽热巴", title="迪丽热巴新剧热播", sentiment="positive", hot_value=9500),
                HotTopic(star_id=2, star_name="杨幂", title="杨幂时尚大片发布", sentiment="positive", hot_value=8800),
                HotTopic(star_id=3, star_name="赵丽颖", title="赵丽颖新作品获得好评", sentiment="positive", hot_value=7500),
                HotTopic(star_id=4, star_name="王一博", title="王一博新舞蹈视频", sentiment="positive", hot_value=6800),
                HotTopic(star_id=5, star_name="肖战", title="肖战新专辑销量破纪录", sentiment="positive", hot_value=5500),
            ]
            db.add_all(sample_topics)

        # 检查关键词
        if db.query(Keyword).count() == 0:
            sample_keywords = [
                Keyword(word="新剧", count=500, sentiment="positive"),
                Keyword(word="支持", count=400, sentiment="positive"),
                Keyword(word="粉丝", count=350, sentiment="positive"),
                Keyword(word="感谢", count=300, sentiment="positive"),
                Keyword(word="努力", count=280, sentiment="positive"),
                Keyword(word="日常", count=200, sentiment="neutral"),
                Keyword(word="分享", count=180, sentiment="neutral"),
                Keyword(word="期待", count=150, sentiment="neutral"),
                Keyword(word="争议", count=50, sentiment="negative"),
                Keyword(word="质疑", count=30, sentiment="negative"),
            ]
            db.add_all(sample_keywords)

        # 检查情感记录
        if db.query(SentimentRecord).count() == 0:
            from datetime import timedelta
            today = datetime.utcnow()
            for i in range(7):
                date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                record = SentimentRecord(
                    star_id=0,  # 全局统计
                    date=date,
                    positive_count=100 + i * 10,
                    neutral_count=50 + i * 5,
                    negative_count=20 + i * 2,
                    total_count=170 + i * 17,
                    avg_score=0.6 + i * 0.02,
                )
                db.add(record)

        db.commit()
    finally:
        db.close()


def get_db():
    """获取数据库会话"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 导出所有表类，供其他模块使用
__all__ = [
    "Base", "Star", "WeiboPost", "HotTopic", "Keyword",
    "SentimentRecord", "Comment", "CollectionTask", "SystemConfig",
    "init_db", "get_db", "SyncSessionLocal"
]