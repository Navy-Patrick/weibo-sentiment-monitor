"""
微博数据采集脚本 - 完整版
采集 100 个帖子，每个帖子 100 条评论
"""
import requests
import json
import time
import sqlite3
import re
import functools
print = functools.partial(print, flush=True)

CDP_PROXY = "http://localhost:3456"
DB_PATH = "C:/test/operation/weibo-sentiment-monitor/backend/services/data.db"
WEIBO_UID = "1776448504"  # 蔡徐坤


def cdp_eval(target_id, script):
    """执行 JS 并返回结果"""
    resp = requests.post(f"{CDP_PROXY}/eval?target={target_id}", data=script)
    result = resp.json()
    if "error" in result:
        return None
    return result.get("value", "")


def cdp_new(url):
    """打开新页面"""
    resp = requests.get(f"{CDP_PROXY}/new?url={url}")
    return resp.json()["targetId"]


def cdp_close(target_id):
    """关闭页面"""
    requests.get(f"{CDP_PROXY}/close?target={target_id}")


def get_posts_list(target_id, count=100):
    """获取帖子列表"""
    all_posts = []
    page = 1

    while len(all_posts) < count:
        url = f"https://weibo.com/ajax/statuses/mymblog?uid={WEIBO_UID}&feature=0&page={page}&count=100&locale=zh-CN"
        script = f'fetch("{url}").then(r=>r.json())'
        result = cdp_eval(target_id, script)

        if not result or not result.get("data"):
            break

        posts = result["data"].get("list", [])
        if not posts:
            break

        for p in posts:
            # 过滤掉转发帖（只保留原创）
            if p.get("retweeted_status"):
                continue

            all_posts.append({
                "id": p.get("idstr", ""),
                "content": re.sub(r'<[^>]+>', '', p.get("text", "")).strip(),
                "comments_count": p.get("comments_count", 0),
                "likes_count": p.get("attitudes_count", 0),
                "reposts_count": p.get("reposts_count", 0),
                "created_at": p.get("created_at", "")
            })

        print(f"  获取第 {page} 页: {len(posts)} 条帖子，累计 {len(all_posts)} 条")
        page += 1

        if len(posts) < 100:  # 最后一页
            break

    return all_posts[:count]


def get_comments(target_id, post_id, count=100):
    """获取帖子评论"""
    all_comments = []
    max_id = None

    while len(all_comments) < count:
        url = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={post_id}&is_show_bulletin=2&is_mix=0&count=20&uid={WEIBO_UID}&fetch_level=0&locale=zh-CN"
        if max_id:
            url += f"&max_id={max_id}"

        script = f'fetch("{url}").then(r=>r.json())'
        result = cdp_eval(target_id, script)

        if not result or result.get("ok") != 1:
            break

        data = result.get("data", [])
        if not data:
            break

        for item in data:
            user = item.get("user", {})
            text = item.get("text", "")
            text = re.sub(r'<[^>]+>', '', text).strip()

            all_comments.append({
                "user": user.get("screen_name", ""),
                "content": text,
                "likes": item.get("like_counts", 0)
            })

        max_id = result.get("max_id")
        if not max_id:
            break

        if len(all_comments) >= count:
            break

        time.sleep(0.3)

    return all_comments[:count]


def save_to_db(posts_data):
    """保存到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取或创建 star
    cursor.execute("SELECT id FROM stars WHERE weibo_id = ?", (WEIBO_UID,))
    row = cursor.fetchone()
    if row:
        star_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO stars (name, weibo_id, fans_count, sentiment_score, status) VALUES (?, ?, ?, ?, ?)",
            ("蔡徐坤", WEIBO_UID, 38780000, 0.5, "active")
        )
        star_id = cursor.lastrowid

    total_comments = 0
    for post in posts_data:
        # 检查帖子是否已存在
        cursor.execute("SELECT id FROM weibo_posts WHERE source LIKE ?", (f"%{post['id']}%",))
        existing = cursor.fetchone()

        if existing:
            post_id = existing[0]
        else:
            cursor.execute(
                """INSERT INTO weibo_posts (star_id, content, sentiment, sentiment_score, likes_count, comments_count, reposts_count, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (star_id, post["content"], "neutral", 0.5, post.get("likes_count", 0), post.get("comments_count", 0), post.get("reposts_count", 0), f"https://weibo.com/{WEIBO_UID}/{post['id']}")
            )
            post_id = cursor.lastrowid

        # 保存评论
        for comment in post.get("comments", []):
            cursor.execute(
                "SELECT id FROM comments WHERE post_id = ? AND user_name = ? AND content = ?",
                (post_id, comment["user"], comment["content"])
            )
            if not cursor.fetchone():
                cursor.execute(
                    """INSERT INTO comments (post_id, user_name, content, likes_count, sentiment, sentiment_score)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (post_id, comment["user"], comment["content"], comment.get("likes", 0), "neutral", 0.5)
                )
                total_comments += 1

        conn.commit()  # 每个帖子提交一次

    conn.close()
    return total_comments


def main():
    print("=" * 60)
    print("微博数据采集脚本 - 完整版")
    print(f"目标: 蔡徐坤 (UID: {WEIBO_UID})")
    print("采集: 100 个帖子，每个帖子 100 条评论")
    print("=" * 60)

    print(f"\n[1] 打开微博页面...")
    target_id = cdp_new(f"https://weibo.com/{WEIBO_UID}")
    time.sleep(5)

    print(f"\n[2] 获取帖子列表...")
    posts = get_posts_list(target_id, count=100)
    print(f"  共获取 {len(posts)} 个帖子")

    print(f"\n[3] 逐个获取评论...")
    for i, post in enumerate(posts):
        print(f"\n  [{i+1}/{len(posts)}] 帖子: {post['content'][:30]}... (评论数: {post['comments_count']})")

        if post['comments_count'] > 0:
            comments = get_comments(target_id, post['id'], count=100)
            post['comments'] = comments
            print(f"    获取到 {len(comments)} 条评论")
        else:
            post['comments'] = []
            print(f"    无评论")

        time.sleep(0.5)

    cdp_close(target_id)

    print(f"\n[4] 保存到数据库...")
    total_comments = save_to_db(posts)
    print(f"  新增 {total_comments} 条评论")

    print("\n" + "=" * 60)
    print("采集完成!")
    print(f"帖子数: {len(posts)}")
    print(f"评论数: {sum(len(p.get('comments', [])) for p in posts)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
