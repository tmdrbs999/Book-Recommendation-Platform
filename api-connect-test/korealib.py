import requests
import pandas as pd
from keybert import KeyBERT
import re
from datetime import datetime

# 🔑 국립중앙도서관 Open API 키와 URL
API_KEY = "4ce21af2f20c58c5eb1924ed81130a54f959ebcc06a16d8eadb23e18c912bb5e"
BASE_URL = "https://www.nl.go.kr/NL/search/openApi/search.do"

# 🔍 1) API에서 데이터 가져오기
def fetch_books(keyword="인공지능"):
    params = {
        "key": API_KEY,
        "kwd": keyword,
        "detailSearch": "true",
        "pageSize": 20
    }
    response = requests.get(BASE_URL, params=params)
    response.encoding = "utf-8"
    
    if response.status_code != 200:
        raise Exception(f"API 요청 실패: {response.status_code}")
    
    # XML → DataFrame 변환
    from xml.etree import ElementTree
    root = ElementTree.fromstring(response.text)
    records = []
    for item in root.iter("item"):
        record = {child.tag: child.text for child in item}
        records.append(record)
    
    return pd.DataFrame(records)

# 🧹 2) 데이터 정제
def clean_books(df):
    df = df.drop_duplicates(subset=["title"], keep="first")
    df["title"] = df["title"].astype(str).str.replace(r"[^가-힣a-zA-Z0-9 ]", "", regex=True)
    df["author"] = df["author"].fillna("미상")
    df["publisher"] = df["publisher"].fillna("미상")
    return df

# 🧠 3) 키워드 추출
def extract_keywords(df):
    kw_model = KeyBERT()
    df["keywords"] = df["title"].apply(lambda x: [kw for kw, _ in kw_model.extract_keywords(x, top_n=3)])
    return df

# 💾 4) 결과 저장
def save_to_csv(df, keyword):
    filename = f"books_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"✅ 결과 저장 완료: {filename}")

# 🚀 실행
if __name__ == "__main__":
    keyword = input("검색어를 입력하세요 (예: 인공지능, 데이터, 경제): ")
    print("📡 국립중앙도서관 API에서 도서 데이터 수집 중...")
    df = fetch_books(keyword)
    print(f"📚 {len(df)}개의 도서 데이터 수집 완료")

    print("🧹 데이터 정제 중...")
    df = clean_books(df)

    print("🧠 키워드 추출 중...")
    df = extract_keywords(df)

    save_to_csv(df, keyword)
