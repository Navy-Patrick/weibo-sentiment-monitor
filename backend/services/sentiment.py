"""
情感分析服务
"""
from snownlp import SnowNLP
import jieba


def analyze_sentiment(text: str) -> dict:
    """分析文本情感"""
    try:
        s = SnowNLP(text)
        score = s.sentiments

        # 根据分数判断情感类型
        if score >= 0.6:
            sentiment = "positive"
        elif score >= 0.4:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        return {
            "sentiment": sentiment,
            "sentiment_score": score,
        }
    except Exception as e:
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.5,
        }


def extract_keywords(text: str, top_n: int = 10) -> list:
    """提取关键词"""
    try:
        # 使用 jieba 分词
        words = jieba.cut(text)
        # 过滤停用词和单字
        stopwords = set(["的", "了", "是", "在", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]

        # 统计词频
        word_count = {}
        for w in keywords:
            word_count[w] = word_count.get(w, 0) + 1

        # 返回前 top_n 个关键词
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [{"word": w, "count": c} for w, c in sorted_words[:top_n]]
    except Exception as e:
        return []