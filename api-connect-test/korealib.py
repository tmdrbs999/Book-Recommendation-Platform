import logging
import requests
import pandas as pd
import re
import psycopg2
from datetime import datetime
from keybert import KeyBERT
import azure.functions as func

# 🔑 PostgreSQL 연결 정보 (환경변수로 설정 권장)
DB_HOST = "YOUR_POSTGRES_HOST"
DB_NAME = "YOUR_DB_NAME"
DB_USER = "YOUR_DB_USER"
DB_PASSWORD = "YOUR_DB_PASSWORD"
DB_PORT = 5432

# 🔑 국립중앙도서관 API
API_URL = "https://www.nl.go.kr/NL/search/openApi/search.do"
API_KEY = "4ce21af2f20c58c5eb1924ed81130a54f959ebcc06a16d8eadb23e18c912bb5e"

def main(mytimer: func.TimerRequest) -> None:
    logging.info("=== Fetching National Library Data... ===")

    # 1️⃣ 데이터 수집
    params = {
        "key": API_KEY,
        "kwd": "인공지능",
        "pageNum": 1,
        "pageSize": 50,
    }
    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        logging.error(f"API 요청 실패: {response.status_code}")
        return
    
    books = response.json().get("docs", [])
    if not books:
        logging.warning("API에서 수집된 데이터가 없습니다.")
        return
    
    df = pd.DataFrame(books)

    # 2️⃣ 데이터 정제
    df = df[["TITLE", "AUTHOR", "PUBLISHER", "SUBJECT", "REG_DATE"]].copy()
    df.columns = ["title", "author", "publisher", "subject", "reg_date"]
    df["title"] = df["title"].apply(lambda x: re.sub(r"[^가-힣a-zA-Z0-9 ]", "", str(x)))
    df["author"] = df["author"].fillna("unknown")
    df.drop_duplicates(subset=["title", "author"], inplace=True)

    # 3️⃣ 키워드 추출 (KeyBERT)
    kw_model = KeyBERT()
    df["keywords"] = df["title"].apply(
        lambda x: [kw for kw, _ in kw_model.extract_keywords(x, top_n=3)]
    )

    # 4️⃣ PostgreSQL 저장
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.library_books (
                id SERIAL PRIMARY KEY,
                title TEXT,
                author TEXT,
                publisher TEXT,
                subject TEXT,
                reg_date TEXT,
                keywords TEXT,
                fetched_at TIMESTAMP
            );
        """)
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.library_books
                (title, author, publisher, subject, reg_date, keywords, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["title"],
                    row["author"],
                    row["publisher"],
                    row["subject"],
                    row["reg_date"],
                    ", ".join(row["keywords"]),
                    datetime.utcnow(),
                ),
            )
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"{len(df)}개 도서 정보가 PostgreSQL에 저장되었습니다.")
    except Exception as e:
        logging.error(f"PostgreSQL 저장 중 오류: {e}")
