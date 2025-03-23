from flask import Flask, jsonify, render_template_string
import requests
import schedule
import threading
import time
import random

app = Flask(__name__)

# 设置多个 NewsAPI 密钥用于轮换
API_KEYS = [
    '0f63de18589144069d67de385b814270',
    '21f1adddc57e484095696916d314f0d5',
    '2420ecf7faff42b19ad050393cd26393'
]
api_key_index = 0

def get_next_api_key():
    global api_key_index
    key = API_KEYS[api_key_index % len(API_KEYS)]
    api_key_index += 1
    return key

# 设置你关注的关键词（包含中文、英文和股票代码）
keywords = [
    "英伟达", "NVIDIA", "NVDA",
    "特斯拉", "Tesla", "TSLA",
    "亚马逊", "Amazon", "AMZN",
    "微软", "Microsoft", "MSFT",
    "台积电", "TSMC", "TSM",
    "博通", "Broadcom", "AVGO",
    "苹果", "Apple", "AAPL"
]

# 按批次划分关键词
keyword_batches = [keywords[i:i+3] for i in range(0, len(keywords), 3)]
current_batch_index = 0

# 存储新闻信息
latest_news = {}

# 免费大模型总结（使用智谱API为例）
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

# 获取新闻函数
def get_latest_stock_news():
    global latest_news, current_batch_index
    latest_news = {}

    # 获取当前批次关键词
    batch = keyword_batches[current_batch_index]
    current_batch_index = (current_batch_index + 1) % len(keyword_batches)

    for keyword in batch:
        api_key = get_next_api_key()
        url = f'https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&apiKey={api_key}'
        try:
            response = requests.get(url)
            time.sleep(1)  # 降低请求频率
            print(f"[{keyword}] 使用API KEY: {api_key[-4:]} 请求状态: {response.status_code}")
            news = response.json()
            print(f"[{keyword}] 返回数据: {news}")
        except Exception as e:
            print(f"[{keyword}] 请求异常: {e}")
            news = {}

        if news.get('status') == 'ok' and 'articles' in news:
            articles = news['articles'][:5]
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('content') or description or title
                article['summary'] = summarize_with_glm(title, description, content)
            latest_news[keyword] = articles
        else:
            print(f"[{keyword}] 未获取到有效新闻数据或状态异常。")
            latest_news[keyword] = []

# 定时任务，每3小时运行一次
schedule.every(3).hours.do(get_latest_stock_news)

# 启动自动任务（后台线程）
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# Web页面展示
@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📈 美股公司最新动态</title>
        <style>
            body {
                font-family: "PingFang SC", "Helvetica Neue", Helvetica, Arial, sans-serif;
                background-color: #f2f2f2;
                margin: 0;
                padding: 1rem;
            }

            h1 {
                text-align: center;
                color: #333;
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
            }

            h2 {
                color: #555;
                margin-top: 2rem;
                font-size: 1.2rem;
                border-left: 4px solid #007bff;
                padding-left: 0.5rem;
            }

            .card {
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                padding: 1rem;
                margin-top: 1rem;
                transition: all 0.2s ease-in-out;
            }

            .card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }

            .summary {
                background-color: #eef9ff;
                border-left: 3px solid #00aaff;
                padding: 0.5rem;
                margin-top: 0.5rem;
                border-radius: 8px;
                font-size: 0.95rem;
            }

            a {
                color: #007bff;
                text-decoration: none;
                word-break: break-word;
            }

            a:hover {
                text-decoration: underline;
            }

            @media (max-width: 600px) {
                h1 {
                    font-size: 1.3rem;
                }
                .card {
                    padding: 0.8rem;
                }
                .summary {
                    font-size: 0.9rem;
                }
            }
        </style>
    </head>
    <body>
        <h1>🚀 美股公司最新动态</h1>
        {% for keyword, articles in news.items() %}
            <h2>{{ keyword }}</h2>
            {% if articles %}
                {% for article in articles %}
                    <div class="card">
                        <strong>📌 标题：</strong>{{ article['title'] }}<br>
                        <strong>📝 描述：</strong>{{ article['description'] }}<br>
                        <strong>📰 来源：</strong>{{ article['source']['name'] }}<br>
                        <strong>🔗 链接：</strong><a href="{{ article['url'] }}" target="_blank">点击查看原文</a><br>
                        <strong>🕒 发布时间：</strong>{{ article['publishedAt'] }}<br>
                        <div class="summary">
                            <strong>🧠 总结：</strong><br>{{ article['summary'] }}
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <p>暂无新闻信息或API请求失败。</p>
            {% endif %}
        {% endfor %}
    </body>
    </html>
    """

    return render_template_string(html, news=latest_news)

if __name__ == '__main__':
    print("🚀 美股公司最新动态监控Web端已启动...")
    get_latest_stock_news()  # 首次启动先运行一次
    app.run(debug=True, host='0.0.0.0', port=5000)
