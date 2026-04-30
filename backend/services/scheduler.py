"""
定时任务调度器
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()


def update_sentiment_data():
    """更新情感数据"""
    print(f"[{datetime.now()}] 正在更新情感数据...")


def crawl_weibo_data():
    """爬取微博数据"""
    print(f"[{datetime.now()}] 正在爬取微博数据...")


def start_scheduler():
    """启动调度器"""
    # 每小时更新情感数据
    scheduler.add_job(update_sentiment_data, 'interval', hours=1)

    # 每天爬取微博数据
    scheduler.add_job(crawl_weibo_data, 'interval', hours=24)

    scheduler.start()
    print("调度器已启动")