import logging
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime, timedelta
import pandas as pd
import math
import re
from collections import Counter
import markdown
import json
import requests

from app_user_keyword.views import filter_dataFrame, api_get_top_userkey
from app_user_keyword_sentiment.views import api_get_userkey_sentiment

# 設定 logger
logger = logging.getLogger(__name__)

# 遠端模型網址與模型名稱
REMOTE_OLLAMA_URL = "http://ollama:11434"
model_name = "gemma3:4b"

logger.info(f"正在連接 {REMOTE_OLLAMA_URL} 檢查可用模型...")
try:
    response = requests.get(f"{REMOTE_OLLAMA_URL}/api/tags")
    models = response.json()
    available_models = [model['name'] for model in models['models']]
    logger.info("可用的模型:")
    for model in available_models:
        logger.info(f"- {model}")
    if model_name in available_models:
        logger.info(f"✅ 模型 '{model_name}' 已可用")
except Exception as e:
    logger.error(f"❌ 無法取得模型列表: {e}")

logger.info("✅ app_user_keyword_llm_report was loaded!")

def home(request):
    return render(request, 'app_user_keyword_llm_report/home.html')

def get_userkey_data(request):
    try:
        logger.info("✅ 收到的 POST 資料：%s", request.POST.dict())
        userkey = request.POST.get('userkey') or '未知主題'
        cate = request.POST.get('cate') or ''
        cond = request.POST.get('cond') or ''
        weeks = int(request.POST.get('weeks', 4))
        key = userkey.split()

        df_query = filter_dataFrame(key, cond, cate, weeks)
        if len(df_query) == 0:
            return {'error': 'No results found for the given keywords.'}

        response_from_sentiment = api_get_userkey_sentiment(request)
        response_from_sentiment = json.loads(response_from_sentiment.content.decode('utf-8'))

        response_from_userkeyword = api_get_top_userkey(request)
        response_from_userkeyword = json.loads(response_from_userkeyword.content.decode('utf-8'))

        return response_from_userkeyword, response_from_sentiment

    except Exception as e:
        logger.exception("❌ get_userkey_data 發生錯誤")
        return {'error': '伺服器處理失敗，請檢查輸入資料或聯絡開發者'}

@csrf_exempt
def api_get_userkey_data(request):
    result = get_userkey_data(request)
    if isinstance(result, dict) and 'error' in result:
        return JsonResponse(result)
    response_from_userkeyword, response_from_sentiment = result
    combined_response = {**response_from_userkeyword, **response_from_sentiment}
    return JsonResponse(combined_response)

@csrf_exempt
def api_get_userkey_llm_report(request):
    import time
    start_time = time.time()

    userkey = request.POST.get('userkey', '未知主題')
    cate = request.POST.get('cate', '')
    cond = request.POST.get('cond', '')
    weeks = request.POST.get('weeks', '4')

    result = get_userkey_data(request)
    if isinstance(result, dict) and 'error' in result:
        return JsonResponse(result, status=400)

    try:
        response_from_userkeyword, response_from_sentiment = result

        key_occurrence_cat = str(response_from_userkeyword.get('key_occurrence_cat', '（無資料）'))[:2000]
        key_time_freq = str(response_from_userkeyword.get('key_time_freq', '（無資料）'))[:2000]
        sentiCount = str(response_from_sentiment.get('sentiCount', '（無資料）'))
        line_data_pos = str(response_from_sentiment.get('data_pos', '（無資料）'))[:1000]
        line_data_neg = str(response_from_sentiment.get('data_neg', '（無資料）'))[:1000]

        system_prompt = f"以下是有關於[{userkey}]的網路聲量資訊，請做一份至少500字的詳細的專業分析報告。請使用繁體中文，並使用Markdown語法。"
        prompt = f'''{system_prompt}\n\n
(1)熱門程度:\n\n{key_occurrence_cat}\n\n
(2)時間趨勢:\n\n{key_time_freq}\n\n
(3)情緒分析比率:\n\n{sentiCount}\n\n
(4)情緒時間變化:\n\n{line_data_pos}\n\n{line_data_neg}
'''

        url = f"{REMOTE_OLLAMA_URL}/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=200)
        response.raise_for_status()

        result = response.json()
        report_text = result.get('response', '⚠️ AI 無內容')

        logger.info("✅ AI 回應成功，長度: %d", len(report_text))
        logger.info("⏱️ 回應耗時: %.2f 秒", time.time() - start_time)
        return JsonResponse({'report': report_text})

    except requests.exceptions.Timeout:
        logger.error("❌ AI 回應 timeout")
        return JsonResponse({'error': 'AI 回應逾時，請稍後再試。'}, status=504)
    except requests.exceptions.RequestException as e:
        logger.error("❌ 呼叫 AI 錯誤: %s", str(e))
        return JsonResponse({'error': 'AI 呼叫失敗，請稍後再試。'}, status=500)
    except json.JSONDecodeError as e:
        logger.error("❌ JSON 解碼錯誤: %s", str(e))
        logger.error("❌ 回傳內容: %s", response.text[:500])
        return JsonResponse({'error': 'AI 回應格式錯誤', 'detail': response.text}, status=500)
    except Exception as e:
        logger.exception("❌ 未知錯誤")
        return JsonResponse({'error': 'AI 發生未知錯誤'}, status=500)
