import os
import sys
import pandas as pd
import pathlib
from datetime import datetime

# 設定 Django 環境
parent_path = pathlib.Path().absolute().parent
sys.path.insert(0, str(parent_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website_configs.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

# 匯入 model
from app_user_keyword_db.models import NewsData

# 讀取 CSV 檔案
csv_file_path = r'/app/app_user_keyword/dataset/yahoo_finace_preprocessed_200.csv'
df = pd.read_csv(csv_file_path, sep='|')

# 初始化計數器
created_count = 0
updated_count = 0

# 遍歷每一筆資料
for idx, row in df.iterrows():
    try:
        date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
        news_data, created = NewsData.objects.update_or_create(
            item_id=row['item_id'],
            defaults={
                'date': date_obj,
                'category': row['category'],
                'title': row['title'],
                'content': row['content'],
                'sentiment': row['sentiment'],
                'top_key_freq': row['top_key_freq'],
                'tokens': row['tokens'],
                'tokens_v2': row['tokens_v2'],
                'entities': row['entities'],
                'token_pos': row['token_pos'],
                'link': row['link'],
                'photo_link': row['photo_link'] if row['photo_link'] != "" and not pd.isna(row['photo_link']) else None,
            }
        )
        if created:
            created_count += 1
        else:
            updated_count += 1
    except Exception as e:
        print(f"❌ Error at row {idx}: {e}")
        print(row)

# 顯示總結
print(f"\n✅ 匯入完成：")
print(f"🆕 新增 {created_count} 筆資料")
print(f"🔁 更新 {updated_count} 筆資料")
