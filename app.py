from flask import Flask, render_template, request, session, redirect, url_for
import requests
import os

app = Flask(__name__)

# 从环境变量获取密钥，如果没有则使用默认值
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-12345')

# 默认股票列表
DEFAULT_STOCKS = ['MSFT', 'GOOGL']

def get_stock_info(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        result = data['chart']['result'][0]
        meta = result['meta']
        
        return {
            'symbol': symbol,
            'price': float(meta['regularMarketPrice']),
            'company_name': meta.get('instrumentInfo', {}).get('shortName', symbol),
            'currency': meta.get('currency', 'USD'),
            'exchange': meta.get('exchangeName', 'N/A')
        }
    except:
        return None

def search_stocks(query):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get('quotes', [])
    except:
        return []

@app.route('/')
def index():
    # 确保 session 中有订阅列表
    if 'subscribed_stocks' not in session:
        session['subscribed_stocks'] = DEFAULT_STOCKS.copy()
    
    # 获取搜索查询
    search_query = request.args.get('search', '')
    search_results = []
    if search_query:
        search_results = search_stocks(search_query)
    
    # 获取已订阅股票的实时信息
    stocks = []
    subscribed = session.get('subscribed_stocks', DEFAULT_STOCKS)
    for symbol in subscribed:
        info = get_stock_info(symbol)
        if info:
            stocks.append(info)
    
    return render_template('index.html', 
                         stocks=stocks,
                         search_query=search_query,
                         search_results=search_results)

@app.route('/subscribe/<symbol>')
def subscribe(symbol):
    stocks = session.get('subscribed_stocks', DEFAULT_STOCKS.copy())
    if symbol not in stocks:
        stocks.append(symbol)
        session['subscribed_stocks'] = stocks
    return redirect(url_for('index'))

@app.route('/unsubscribe/<symbol>')
def unsubscribe(symbol):
    stocks = session.get('subscribed_stocks', [])
    if symbol in stocks:
        stocks.remove(symbol)
        session['subscribed_stocks'] = stocks
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 根据环境变量决定运行模式
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 