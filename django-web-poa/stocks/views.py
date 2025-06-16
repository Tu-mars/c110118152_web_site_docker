import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from datetime import datetime
import yfinance as yf 
import re, json
import time
API_KEY = '5CGCZY2DKWHK0SV8'  # 替換為你的 API 金鑰

def combined_stock_view(request):
    stock_charts = []
    error_list = []

    if request.method == 'POST':
        symbol_input = request.POST.get('symbol').strip()
        symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]

        for symbol in symbols:
            try:
                is_tw = symbol.isdigit()
                ticker_symbol = f"{symbol}.TW" if is_tw else symbol
                ticker = yf.Ticker(ticker_symbol)
                time.sleep(1.5)
                hist = ticker.history(period="100d")

                if hist.empty:
                    error_list.append(f"{symbol} 查無資料")
                    continue

                dates = [d.strftime('%m-%d') for d in hist.index]
                prices = [round(p, 2) for p in hist['Close']]
                change = prices[-1] - prices[0]
                percent = (change / prices[0]) * 100 if prices[0] != 0 else 0
                
                stock_charts.append({
                    'symbol': symbol,
                    'market': '台股' if is_tw else '美股',
                    'dates': dates,
                    'prices': prices,
                    'latest_price': prices[-1],
                    'change': round(change, 2),
                    'percent': round(percent, 2),
                    'positive': change >= 0
                })

            except Exception as e:
                error_list.append(f"{symbol} 發生錯誤：{type(e).__name__}: {str(e)}")

    # 加入指數資訊
    index_symbols = {
        '台股加權指數': '^TWII',
        '道瓊工業指數': '^DJI',
        '標普500指數': '^GSPC',
        '那斯達克指數': '^IXIC',
    }
    index_cards = []

    for name, code in index_symbols.items():
        try:
            ticker = yf.Ticker(code)
            time.sleep(1.5)
            data = ticker.history(period='1d')
            if data.empty:
                continue
            latest = data.iloc[-1]
            price = round(latest['Close'], 2)
            change = round(latest['Close'] - latest['Open'], 2)
            change_percent = round((change / latest['Open']) * 100, 2)

            index_cards.append({
                'name': name,
                'price': price,
                'change': change,
                'percent': change_percent,
                'positive': change >= 0
            })
        except Exception:
            continue

    return render(request, 'stocks/quote.html', {
        'stock_charts': stock_charts,
        'index_cards': index_cards,
        'error': '<br>'.join(error_list) if error_list else None
    })