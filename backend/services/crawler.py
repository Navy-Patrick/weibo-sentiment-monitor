"""
微博 CDP 爬虫服务
基于 Chrome DevTools Protocol Proxy 实现数据采集
不依赖截图，纯文本 DOM 提取
"""
import requests
import json
import time
import threading
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# 数据库配置
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
sync_engine = create_engine(f"sqlite:///{DB_PATH}")
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 导入表结构（延迟导入避免循环依赖）
Base = declarative_base()

class Star(Base):
    __tablename__ = "stars"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    weibo_id = Column(String(100))
    fans_count = Column(Integer)
    sentiment_score = Column(Float)
    status = Column(String(20))

class WeiboPost(Base):
    __tablename__ = "weibo_posts"
    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)
    content = Column(Text)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    likes_count = Column(Integer)
    comments_count = Column(Integer)
    reposts_count = Column(Integer)
    source = Column(String(500))

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer)
    user_name = Column(String(100))
    content = Column(Text)
    likes_count = Column(Integer)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    publish_time = Column(String(50))

class CollectionTask(Base):
    __tablename__ = "collection_tasks"
    id = Column(Integer, primary_key=True, index=True)
    star_id = Column(Integer)
    weibo_uid = Column(String(100))
    posts_count = Column(Integer)
    comments_count = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

CDP_PROXY = "http://localhost:3456"

# 全局采集状态
_current_task = None
_stop_flag = False


def get_current_task():
    """获取当前采集任务状态"""
    return _current_task


def set_stop_flag(value: bool):
    """设置停止标志"""
    global _stop_flag
    _stop_flag = value


def _cdp_request(method: str, target_id: str = None, data: str = None, url: str = None):
    """统一的 CDP API 请求"""
    if url:
        resp = requests.get(f"{CDP_PROXY}/{method}?url={url}")
    elif target_id and data:
        resp = requests.post(f"{CDP_PROXY}/{method}?target={target_id}", data=data)
    elif target_id:
        resp = requests.get(f"{CDP_PROXY}/{method}?target={target_id}")
    else:
        resp = requests.get(f"{CDP_PROXY}/{method}")

    if resp.status_code != 200:
        raise Exception(f"CDP request failed: {resp.text}")
    return resp.json()


def _eval_js(target_id: str, script: str) -> str:
    """执行 JS 并返回结果"""
    resp = requests.post(f"{CDP_PROXY}/eval?target={target_id}", data=script)
    result = resp.json()
    if "error" in result:
        raise Exception(f"JS eval error: {result['error']}")
    return result.get("value", "")


def fetch_star_info(weibo_uid: str) -> dict:
    """
    获取明星个人信息
    返回：昵称、粉丝数、简介等
    """
    url = f"https://weibo.com/u/{weibo_uid}"

    # 打开页面
    result = _cdp_request("new", url=url)
    target_id = result["targetId"]

    # 等待加载
    time.sleep(3)

    # 提取信息 - 单行脚本避免转义问题
    script = 'JSON.stringify({nickname:document.querySelector("[class*=name]")?.innerText?.trim()||"",fans_count:(()=>{const els=document.querySelectorAll("a,span,div");for(const el of els){const t=el.innerText;if(t&&t.includes("粉丝")&&!t.includes("转评赞")){const m=t.match(/[0-9]+/);if(m){let n=parseInt(m[0]);if(t.includes("万"))n*=10000;if(t.includes("亿"))n*=100000000;return n;}}}return 0;})()})'

    info_str = _eval_js(target_id, script)
    info = json.loads(info_str)

    # 关闭页面
    _cdp_request("close", target_id=target_id)

    return info


def fetch_posts_list(weibo_uid: str, count: int = 100) -> list:
    """
    获取用户的帖子列表
    返回帖子 URL 列表
    """
    url = f"https://weibo.com/u/{weibo_uid}"

    # 打开用户主页
    result = _cdp_request("new", url=url)
    target_id = result["targetId"]

    time.sleep(5)

    posts = []
    scroll_count = 0
    max_scrolls = 30  # 最大滚动次数

    # 单行脚本提取帖子链接
    script = 'JSON.stringify([...document.querySelectorAll("a")].map(a=>a.href).filter(h=>{try{const url=new URL(h);return url.hostname==="weibo.com"&&url.pathname.split("/").length===3&&url.pathname.split("/")[2].length===9}catch(e){return false}}))'

    while len(posts) < count and scroll_count < max_scrolls:
        links_str = _eval_js(target_id, script)
        try:
            new_links = json.loads(links_str)
        except:
            new_links = []

        for link in new_links:
            if link not in posts:
                posts.append(link)

        if len(posts) >= count:
            break

        # 滚动加载更多
        _cdp_request("scroll", target_id=target_id, y="3000")
        scroll_count += 1
        time.sleep(2)

    # 关闭页面
    _cdp_request("close", target_id=target_id)

    return posts[:count]


def fetch_post_detail(post_url: str) -> dict:
    """
    获取帖子详情
    返回：内容、作者、点赞数、评论数、转发数
    """
    result = _cdp_request("new", url=post_url)
    target_id = result["targetId"]

    time.sleep(3)

    # 单行脚本提取帖子详情
    script = 'JSON.stringify({content:document.querySelector(".wbpro-feed-content")?.innerText?.trim()||"",author:document.querySelector("[class*=name]")?.innerText?.trim()||"",likes:0,comments:0,reposts:0})'

    post_str = _eval_js(target_id, script)
    try:
        post = json.loads(post_str)
    except:
        post = {"content": "", "author": "", "likes": 0, "comments": 0, "reposts": 0}

    # 关闭页面
    _cdp_request("close", target_id=target_id)

    return post


def fetch_post_comments(post_url: str, count: int = 100) -> list:
    """
    获取帖子评论
    返回评论列表
    """
    result = _cdp_request("new", url=post_url)
    target_id = result["targetId"]

    time.sleep(3)

    # 滚动加载评论
    scroll_count = 0
    max_scrolls = 20

    # 先滚动几次触发评论加载
    while scroll_count < 3:
        _cdp_request("scroll", target_id=target_id, y="2000")
        scroll_count += 1
        time.sleep(1)

    comments = []

    # 单行脚本提取评论
    script = 'JSON.stringify([...document.querySelectorAll(".wbpro-scroller-item")].map(el=>el.innerText).filter(t=>t&&t.includes("来自")).map(t=>{const m=t.match(/^(.+?)\\s*:\\s*(.+?)\\s*[0-9]+-[0-9]+-[0-9]+/);return m?{user_name:m[1].trim(),content:m[2].trim()}:null}).filter(c=>c))'

    while len(comments) < count and scroll_count < max_scrolls:
        comments_str = _eval_js(target_id, script)
        try:
            new_comments = json.loads(comments_str)
        except:
            new_comments = []

        for c in new_comments:
            if c.get("user_name") and c.get("content"):
                # 检查是否已存在（去重）
                exists = any(
                    existing["user_name"] == c["user_name"] and existing["content"] == c["content"]
                    for existing in comments
                )
                if not exists:
                    comments.append(c)

        if len(comments) >= count:
            break

        _cdp_request("scroll", target_id=target_id, y="2000")
        scroll_count += 1
        time.sleep(2)

    # 关闭页面
    _cdp_request("close", target_id=target_id)

    return comments[:count]


def analyze_sentiment(text: str) -> tuple:
    """
    简单情感分析
    返回 (sentiment, score)
    """
    # 使用关键词判断
    positive_words = ["支持", "喜欢", "爱", "棒", "赞", "期待", "加油", "感谢", "优秀", "好看", "精彩"]
    negative_words = ["质疑", "批评", "差", "烂", "无聊", "失望", "糟糕", "恶心", "讨厌", "反感"]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    if pos_count > neg_count:
        return ("positive", 0.6 + pos_count * 0.1)
    elif neg_count > pos_count:
        return ("negative", 0.4 - neg_count * 0.1)
    else:
        return ("neutral", 0.5)


def run_collection_task(
    weibo_uid: str,
    posts_count: int = 100,
    comments_per_post: int = 100,
    task_id: int = None
):
    """
    执行完整采集任务（异步运行）
    """
    global _current_task, _stop_flag

    db = SyncSessionLocal()

    try:
        # 更新任务状态
        if task_id:
            task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
            if task:
                task.status = "running"
                task.started_at = datetime.utcnow()
                db.commit()

        _current_task = {
            "is_running": True,
            "weibo_uid": weibo_uid,
            "posts_fetched": 0,
            "comments_fetched": 0,
            "current_post": "",
            "error": None
        }
        _stop_flag = False

        # 1. 获取明星信息
        star_info = fetch_star_info(weibo_uid)

        # 创建或更新明星记录
        star = db.query(Star).filter(Star.weibo_id == weibo_uid).first()
        if not star:
            star = Star(
                name=star_info.get("nickname", weibo_uid),
                weibo_id=weibo_uid,
                fans_count=star_info.get("fans_count", 0),
                sentiment_score=0.5,
                status="active"
            )
            db.add(star)
            db.commit()
            db.refresh(star)
        else:
            star.fans_count = star_info.get("fans_count", 0)
            star.name = star_info.get("nickname", star.name)
            db.commit()

        if task_id:
            task.star_id = star.id
            db.commit()

        # 2. 获取帖子列表
        post_urls = fetch_posts_list(weibo_uid, posts_count)

        total_comments = 0

        # 3. 逐个帖子采集详情和评论
        for i, post_url in enumerate(post_urls):
            if _stop_flag:
                if task_id:
                    task.status = "stopped"
                    task.completed_at = datetime.utcnow()
                    db.commit()
                break

            _current_task["current_post"] = post_url

            # 获取帖子详情
            post_detail = fetch_post_detail(post_url)

            # 保存帖子
            sentiment, score = analyze_sentiment(post_detail.get("content", ""))

            # 检查是否已存在
            existing_post = db.query(WeiboPost).filter(
                WeiboPost.star_id == star.id,
                WeiboPost.content == post_detail.get("content", "")
            ).first()

            if not existing_post:
                weibo_post = WeiboPost(
                    star_id=star.id,
                    content=post_detail.get("content", ""),
                    sentiment=sentiment,
                    sentiment_score=score,
                    likes_count=post_detail.get("likes", 0),
                    comments_count=post_detail.get("comments", 0),
                    reposts_count=post_detail.get("reposts", 0),
                    source=post_url
                )
                db.add(weibo_post)
                db.commit()
                db.refresh(weibo_post)
            else:
                weibo_post = existing_post

            _current_task["posts_fetched"] = i + 1

            # 4. 获取评论
            if comments_per_post > 0:
                comments = fetch_post_comments(post_url, comments_per_post)

                for comment in comments:
                    if _stop_flag:
                        break

                    c_sentiment, c_score = analyze_sentiment(comment.get("content", ""))

                    # 检查是否已存在
                    existing_comment = db.query(Comment).filter(
                        Comment.post_id == weibo_post.id,
                        Comment.user_name == comment.get("user_name"),
                        Comment.content == comment.get("content")
                    ).first()

                    if not existing_comment:
                        new_comment = Comment(
                            post_id=weibo_post.id,
                            user_name=comment.get("user_name", ""),
                            content=comment.get("content", ""),
                            likes_count=comment.get("likes_count", 0),
                            sentiment=c_sentiment,
                            sentiment_score=c_score,
                            publish_time=comment.get("publish_time", "")
                        )
                        db.add(new_comment)
                        total_comments += 1

                db.commit()
                _current_task["comments_fetched"] = total_comments

            # 控制频率，避免风控
            time.sleep(2)

        # 完成任务
        if task_id and not _stop_flag:
            task.status = "completed"
            task.posts_count = _current_task["posts_fetched"]
            task.comments_count = _current_task["comments_fetched"]
            task.completed_at = datetime.utcnow()
            db.commit()

        _current_task["is_running"] = False

    except Exception as e:
        _current_task["is_running"] = False
        _current_task["error"] = str(e)

        if task_id:
            task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()

    finally:
        db.close()


def start_async_collection(
    weibo_uid: str,
    posts_count: int = 100,
    comments_per_post: int = 100
) -> int:
    """
    启动异步采集任务
    返回任务 ID
    """
    db = SyncSessionLocal()

    # 创建任务记录
    task = CollectionTask(
        weibo_uid=weibo_uid,
        posts_count=posts_count,
        comments_count=comments_per_post,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id
    db.close()

    # 启动后台线程
    thread = threading.Thread(
        target=run_collection_task,
        args=(weibo_uid, posts_count, comments_per_post, task_id),
        daemon=True
    )
    thread.start()

    return task_id