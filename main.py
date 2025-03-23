from flask import Flask, render_template_string
import requests
import time

app = Flask(__name__)

# 设置关键词和映射
stock_tabs = {
    "英伟达": ["英伟达", "NVIDIA", "NVDA"],
    # "特斯拉": ["特斯拉", "Tesla", "TSLA"],
    #"亚马逊": ["亚马逊", "Amazon", "AMZN"],
    # "苹果": ["苹果", "Apple", "AAPL"],
    #"微软": ["微软", "Microsoft", "MSFT"],
    # "台积电": ["台积电", "TSMC", "TSM"],
    #"博通": ["博通", "Broadcom", "AVGO"]
}

stock_code_map = {
    "英伟达": "NVDA",
    #"特斯拉": "TSLA",
    # "亚马逊": "AMZN",
    # "苹果": "AAPL",
    # "微软": "MSFT",
    #"台积电": "TSM",
    # "博通": "AVGO"
}

GNEWS_API_KEY = '118ccae9bbb57ed0e4e5c9b7f807a3fb'

# 新闻数据
latest_news = {}

# 智谱GLM总结（可选）
def summarize(title, description, content):
    return description or title

# 获取新闻
def get_news():
    global latest_news
    latest_news = {}
    for group, keywords in stock_tabs.items():
        all_articles = []
        for keyword in keywords:
            url = f'https://gnews.io/api/v4/search?q={keyword}&lang=zh&max=3&token={GNEWS_API_KEY}'
            try:
                r = requests.get(url)
                if r.status_code == 200 and r.json().get("articles"):
                    for art in r.json()["articles"]:
                        content = art.get("content") or art.get("description", "")
                        art["summary"] = summarize(art.get("title", ""), art.get("description", ""), content)
                        all_articles.append(art)
            except:
                continue
        latest_news[group] = all_articles[:5]

# 抓一次新闻
get_news()

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8">
      <title>🚀 美股公司最新动态</title>
      <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 1rem; }
        h1 { text-align: center; }
        .tabs { display: flex; justify-content: center; flex-wrap: wrap; margin: 1rem 0; }
        .tab { padding: 8px 16px; margin: 4px; background: #fff; border-radius: 5px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .tab.active { background: #2e90fa; color: #fff; }
        .company-section { display: none; }
        .company-section.active { display: block; }
        .card { background: #fff; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
        .card h3 { margin: 0; font-size: 1.1rem; }
        .card p { font-size: 0.95rem; color: #444; }
        .card a { font-size: 0.9rem; color: #2e90fa; text-decoration: none; }
        .trend { text-align: center; margin-bottom: 1rem; }
      </style>
    </head>
    <body>
      <h1>🚀 美股公司最新动态</h1>
      <div class="tabs">
        {% for tab in stock_tabs %}
          <div class="tab" onclick="switchTab('{{ tab }}')">{{ tab }}</div>
        {% endfor %}
      </div>

      {% for tab in stock_tabs %}
        <div id="tab-{{ tab }}" class="company-section">
          <div class="trend">
            <img src="https://chart.finance.yahoo.com/z?s={{ stock_code_map[tab] }}&t=1d&q=l&l=on&z=s&p=m50" width="320">
          </div>
          {% if news[tab] %}
            {% for article in news[tab] %}
              <div class="card">
                <h3>{{ loop.index }}. 📰 {{ article['title'] }}</h3>
                <p>📍 {{ article['source']['name'] }} | 🕒 {{ article['publishedAt'][:10] }}</p>
                <p>💡 {{ article['summary'] }}</p>
                <a href="{{ article['url'] }}" target="_blank">🔗 查看原文</a>
              </div>
            {% endfor %}
          {% else %}
            <p>暂无新闻</p>
          {% endif %}
        </div>
      {% endfor %}

      <script>
        function switchTab(name) {
          document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
          document.querySelectorAll('.company-section').forEach(c => c.classList.remove('active'));
          document.querySelectorAll('.tab').forEach(t => { if(t.innerText === name) t.classList.add('active'); });
          document.getElementById('tab-' + name).classList.add('active');
        }
        switchTab('英伟达');
      </script>
    </body>
    </html>
    """
    return render_template_string(html, news=latest_news, stock_tabs=stock_tabs, stock_code_map=stock_code_map)

if __name__ == "__main__":
    print("🚀 美股公司最新动态监控Web端已启动...")
    app.run(debug=True, port=5001)
