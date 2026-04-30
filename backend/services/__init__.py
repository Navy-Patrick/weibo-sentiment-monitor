"""服务模块"""
from .database import init_db, get_db, Star, WeiboPost, HotTopic, Keyword, SentimentRecord
from .sentiment import analyze_sentiment, extract_keywords
from .scheduler import start_scheduler

__all__ = ["init_db", "get_db", "Star", "WeiboPost", "HotTopic", "Keyword", "SentimentRecord", "analyze_sentiment", "extract_keywords", "start_scheduler"]