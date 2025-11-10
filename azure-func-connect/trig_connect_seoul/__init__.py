import logging
import azure.functions as func
import requests
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import os
import re
import tempfile
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# === 1. Session 생성 함수 ===
def build_session(total_retries: int = 3, backoff: float = 1.0) -> requests.Session:
    s = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    return s


# === 2. JSON/텍스트 파싱 유틸 ===
def extract_by_path(obj, path: str):
    if not path:
        return obj
    cur = obj
    for p in path.split('.'):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def parse_wage(text):
    """시급/월급 문자열 파싱"""
    if not isinstance(text, str):
        return {'wage_type': None, 'wage_value_krw': None, 'wage_raw': text}
    s = text.strip()
    m = re.search(r'\(?(월급|시급)\)?\s*[/\\]?\s*([0-9,\.]+)\s*(만원|원)?', s)
    if m:
        wtype, num, unit = m.group(1), m.group(2), m.group(3) or '원'
        try:
            num_val = int(float(num.replace(',', '')))
        except Exception:
            num_val = None
        value = num_val * 10000 if unit == '만원' else num_val
        return {'wage_type': wtype, 'wage_value_krw': value, 'wage_raw': text}
    m2 = re.search(r'([0-9,\.]+)\s*(만원|원)', s)
    if m2:
        try:
            num_val = int(float(m2.group(1).replace(',', '')))
        except Exception:
            num_val = None
        unit = m2.group(2)
        value = num_val * 10000 if unit == '만원' else num_val
        wtype = '월급' if '월' in s else ('시급' if '시' in s else None)
        return {'wage_type': wtype, 'wage_value_krw': value, 'wage_raw': text}
    return {'wage_type': None, 'wage_value_krw': None, 'wage_raw': text}


def parse_gui_ln(gui):
    """GUI_LN 문자열에서 지역(region)과 경력(career) 추출"""
    if not isinstance(gui, str):
        return {'region': None, 'career': None, 'gui_raw': gui}
    parts = [p.strip() for p in gui.split('/')]
    region = parts[1] if len(parts) >= 2 else None
    career = parts[2] if len(parts) >= 3 else None
    return {'region': region, 'career': career, 'gui_raw': gui}


# === 3. API 호출 ===
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

        records = extract_by_path(data, "GetJobInfo.row")
        records = ensure_list(records)
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


# === 4. 데이터 정제 ===
def clean_dataframe(df: pd.DataFrame, convert_monthly: bool = True, hours_per_month: int = 209) -> pd.DataFrame:
    keep = [
        'CMPNY_NM', 'JO_SJ', 'HOPE_WAGE', 'GUI_LN',
        'RCRIT_JSSFC_CMMN_CODE_SE', 'JOBCODE_NM', 'CAREER_CND_CMMN_CODE_SE', 'ACDMCR_CMMN_CODE_SE'
    ]
    existing = [c for c in keep if c in df.columns]
    out = df[existing].copy()
    out = out.rename(columns={
        'CMPNY_NM': 'company',
        'JO_SJ': 'job_title',
        'HOPE_WAGE': 'hope_wage',
        'GUI_LN': 'gui_ln'
    })

    wage_df = pd.DataFrame(out['hope_wage'].fillna('').apply(parse_wage).tolist(), index=out.index)
    gui_df = pd.DataFrame(out['gui_ln'].fillna('').apply(parse_gui_ln).tolist(), index=out.index)

    out = pd.concat([out, wage_df, gui_df], axis=1)

    if convert_monthly:
        def to_monthly(row):
            if row.get('wage_type') == '시급' and row.get('wage_value_krw'):
                return int(row['wage_value_krw'] * hours_per_month)
            if row.get('wage_type') == '월급' and row.get('wage_value_krw'):
                return int(row['wage_value_krw'])
            return None
        out['wage_value_monthly'] = out.apply(to_monthly, axis=1)

    return out


# === 5. Azure Function main ===
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP Trigger 시작: 서울시 일자리 API 데이터 수집")

    try:
        # (1) 요청 파라미터
        industry = req.params.get("industry", "J01302")
        max_records = int(req.params.get("max_records", "200"))
        api_key = os.getenv("SEOUL_API_KEY", "인증키")
        blob_conn_str = os.getenv("AzureWebJobsStorage")
        container_name = os.getenv("BLOB_CONTAINER_NAME", "seoul-job-ct")

        # (2) API 호출
        session = build_session()
        records = fetch_seoul_jobs(session, api_key, industry, max_records=max_records)
        if not records:
            return func.HttpResponse("⚠️ API 응답에 데이터가 없습니다.", status_code=200)

        df = pd.DataFrame(records)
        clean_df = clean_dataframe(df, convert_monthly=True)

        # (3) 최종 필터링 컬럼만 남기기
        filtered_cols = [
            'company', 'job_title', 'wage_type', 'wage_value_krw', 'region', 'career',
            'RCRIT_JSSFC_CMMN_CODE_SE', 'JOBCODE_NM', 'CAREER_CND_CMMN_CODE_SE', 'ACDMCR_CMMN_CODE_SE'
        ]
        for c in filtered_cols:
            if c not in clean_df.columns:
                clean_df[c] = None
        filtered_df = clean_df[filtered_cols].copy()

        # (4) CSV 생성 및 Blob 업로드
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "seoul_jobs_filtered.csv")
            filtered_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

            blob_service_client = BlobServiceClient.from_connection_string(blob_conn_str)
            container_client = blob_service_client.get_container_client(container_name)
            try:
                container_client.create_container()
            except Exception:
                pass

            file_name = f"seoul_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            blob_client = container_client.get_blob_client(file_name)
            csv_bytes = filtered_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            blob_client.upload_blob(csv_bytes, overwrite=True)
            logging.info(f"✅ Blob 업로드 완료: {file_name}")

        return func.HttpResponse(f"✅ 업로드 성공: {file_name}", status_code=200)

    except Exception as e:
        logging.error(f"❌ 오류 발생: {e}")
        return func.HttpResponse(f"서버 오류: {e}", status_code=500)
