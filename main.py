from flask import Flask, jsonify, render_template_string
import requests
import schedule
import threading
import time

app = Flask(__name__)

# 设置关键词（中英文+股票代码）
keywords = [
    "英伟达", "NVIDIA", "NVDA",
    "特斯拉", "Tesla", "TSLA",
    "亚马逊", "Amazon", "AMZN",
    "微软", "Microsoft", "MSFT",
    "台积电", "TSMC", "TSM",
    "博通", "Broadcom", "AVGO",
    "苹果", "Apple", "AAPL"
]

# GNews API Key
GNEWS_API_KEY = '118ccae9bbb57ed0e4e5c9b7f807a3fb'

# 按批次划分关键词
keyword_batches = [keywords[i:i+3] for i in range(0, len(keywords), 3)]
current_batch_index = 0

# 新闻存储
latest_news = {}

# 使用智谱 GLM 总结文章
def summarize_with_glm(title, description, content):
    try:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 6a6c86f181a84da6b8e315b2b377c890.fHqPDniu4vA2Z4SF"
        }
        full_text = f"请基于以下财经新闻，提炼3条关键信息，简洁准确地总结事件核心，避免重复，适合投资者快速浏览：\n\n标题：{title}\n\n描述：{description}\n\n正文：{content}"
        data = {
            "model": "glm-4",
            "messages": [
                {"role": "user", "content": full_text}
            ]
        }
        resp = requests.post(url, headers=headers, json=data).json()
        return resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"总结失败：{e}"

# 获取新闻数据（来自 GNews API）
def get_latest_stock_news():
    global latest_news, current_batch_index
    latest_news = {}

    batch = keyword_batches[current_batch_index]
    current_batch_index = (current_batch_index + 1) % len(keyword_batches)

    for keyword in batch:
        url = f'https://gnews.io/api/v4/search?q={keyword}&lang=zh&max=5&token={GNEWS_API_KEY}'
        try:
            response = requests.get(url)
            time.sleep(1)
            print(f"[{keyword}] 请求状态: {response.status_code}")
            news = response.json()
            print(f"[{keyword}] 返回数据: {news}")
        except Exception as e:
            print(f"[{keyword}] 请求异常: {e}")
            news = {}

        if news.get('articles'):
            articles = news['articles'][:5]
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('content') or description or title
                article['summary'] = summarize_with_glm(title, description, content)
            latest_news[keyword] = articles
        else:
            print(f"[{keyword}] 暂无新闻信息或API请求失败。")
            latest_news[keyword] = []

# 每3小时执行一次
schedule.every(3).hours.do(get_latest_stock_news)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

@app.route('/')
def index():
    html = """
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>🚀 美股公司最新动态</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      background-color: #f4f4f4;
      margin: 0;
      padding: 1rem;
    }
    h1 {
      text-align: center;
      color: #222;
      margin-bottom: 2rem;
    }
    .company-section {
      margin-bottom: 2rem;
    }
    .company-title {
      font-size: 1.2rem;
      font-weight: bold;
      color: #333;
      border-left: 4px solid #2e90fa;
      padding-left: 0.5rem;
      margin-bottom: 1rem;
    }
    .card {
      background-color: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      padding: 1rem;
      margin-bottom: 1rem;
    }
    .card h3 {
      margin: 0 0 0.3rem;
      font-size: 1rem;
      color: #222;
    }
    .card p {
      margin: 0.3rem 0;
      font-size: 0.95rem;
      color: #444;
    }
    .card a {
      color: #2e90fa;
      text-decoration: none;
      font-size: 0.9rem;
    }
    .no-data {
      font-size: 0.95rem;
      color: #888;
      margin-left: 0.5rem;
    }
  </style>
</head>
<body>
  <h1>🚀 美股公司最新动态</h1>
  {% for keyword, articles in news.items() %}
    <div class="company-section">
      <div class="company-title">{{ keyword }}</div>
      {% if articles %}
        {% for article in articles %}
          <div class="card">
            <h3>📰 {{ article['title'] }}</h3>
            <p>📍 {{ article['source']['name'] }} | 🕒 {{ article['publishedAt'][:10] }}</p>
            <p>💡 {{ article['summary'] }}</p>
            <a href="{{ article['url'] }}" target="_blank">🔗 查看原文</a>
          </div>
        {% endfor %}
      {% else %}
        <p class="no-data">暂无新闻信息或API请求失败。</p>
      {% endif %}
    </div>
  {% endfor %}
</body>
</html>
"""

    return render_template_string(html, news=latest_news)

if __name__ == '__main__':
    print("🚀 美股公司最新动态监控Web端已启动...")
    get_latest_stock_news()
    app.run(debug=True, host='0.0.0.0', port=5000)
