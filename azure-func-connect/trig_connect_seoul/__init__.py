import logging
import azure.functions as func
import requests
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# === 1. Session 생성 함수 ===
def build_session(total_retries: int = 3, backoff: float = 1.0) -> requests.Session:
    session = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


# === 2. API 요청 함수 ===
def fetch_seoul_jobs(session: requests.Session, api_key: str, industry: str, chunk_size: int = 100, max_records: int | None = None):
    all_rec = []
    start = 1
    while True:
        end = start + chunk_size - 1
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/GetJobInfo/{start}/{end}//{industry}"
        logging.info(f"요청 중: {url}")
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logging.error(f"요청 실패: {e}")
            break

        records = data.get("GetJobInfo", {}).get("row", [])
        if not records:
            break
        all_rec.extend(records)
        if max_records and len(all_rec) >= max_records:
            all_rec = all_rec[:max_records]
            break
        if len(records) < chunk_size:
            break
        start = end + 1

    return all_rec


# === 3. 데이터 정제 ===
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = ["CMPNY_NM", "JO_SJ", "HOPE_WAGE", "GUI_LN"]
    df = df[keep_cols].rename(columns={
        "CMPNY_NM": "company",
        "JO_SJ": "job_title",
        "HOPE_WAGE": "hope_wage",
        "GUI_LN": "gui_ln"
    })
    return df


# === 4. Azure Function Main ===
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP Trigger 시작: 서울시 일자리 API 데이터 수집")

    try:
        # --- (1) 요청 파라미터 ---
        industry = req.params.get("industry", "J01302")  # 기본 산업 코드
        max_records = int(req.params.get("max_records", "200"))
        api_key = os.getenv("SEOUL_API_KEY", "인증키")

        # --- (2) API 호출 ---
        session = build_session()
        records = fetch_seoul_jobs(session, api_key, industry, max_records=max_records)
        if not records:
            return func.HttpResponse("⚠️ API 응답에 데이터가 없습니다.", status_code=200)

        df = pd.DataFrame(records)
        df_clean = clean_dataframe(df)

        # --- (3) Blob 업로드 ---
        blob_conn_str = os.getenv("AzureWebJobsStorage")
        container_name = os.getenv("BLOB_CONTAINER_NAME", "seoul-job-data")

        blob_service_client = BlobServiceClient.from_connection_string(blob_conn_str)
        container_client = blob_service_client.get_container_client(container_name)
        try:
            container_client.create_container()
        except Exception:
            pass

        file_name = f"seoul_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        blob_client = container_client.get_blob_client(file_name)
        csv_bytes = df_clean.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

        blob_client.upload_blob(csv_bytes, overwrite=True)
        logging.info(f"✅ 업로드 완료: {file_name}")

        return func.HttpResponse(f"업로드 성공: {file_name}", status_code=200)

    except Exception as e:
        logging.error(f"오류 발생: {e}")
        return func.HttpResponse(f"서버 오류: {e}", status_code=500)
