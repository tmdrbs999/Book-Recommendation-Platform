from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_KEY = '56414b5666746d6437357572434246'  


def build_session(total_retries: int = 3, backoff: float = 1.0) -> requests.Session:
    s = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    return s


def get_json(session: requests.Session, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Any:
    try:
        resp = session.get(url, params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print('Request error:', e, file=sys.stderr)
        raise


def extract_by_path(obj: Any, path: str):
    if not path:
        return obj
    parts = path.split('.')
    cur = obj
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def ensure_list(x: Any) -> List:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def parse_wage(text: Any) -> Dict[str, Any]:
    if not isinstance(text, str):
        return {'wage_type': None, 'wage_value_krw': None, 'wage_raw': text}
    s = text.strip()
    # common patterns: (월급)210만원, (시급)10030원, 월급 / 210만원, 시급 / 10030원
    m = re.search(r'\(?(월급|시급)\)?\s*[/\\]?\s*([0-9,\.]+)\s*(만원|원)?', s)
    if m:
        wtype = m.group(1)
        num = m.group(2)
        unit = m.group(3) or '원'
        try:
            num_val = int(float(num.replace(',', '')))
        except Exception:
            num_val = None
        if num_val is None:
            return {'wage_type': wtype, 'wage_value_krw': None, 'wage_raw': text}
        if unit == '만원':
            value = num_val * 10000
        else:
            value = num_val
        return {'wage_type': wtype, 'wage_value_krw': value, 'wage_raw': text}
    # fallback: find number with 만원 or 원
    m2 = re.search(r'([0-9,\.]+)\s*(만원|원)', s)
    if m2:
        try:
            num_val = int(float(m2.group(1).replace(',', '')))
        except Exception:
            num_val = None
        unit = m2.group(2)
        if num_val is None:
            return {'wage_type': None, 'wage_value_krw': None, 'wage_raw': text}
        if unit == '만원':
            value = num_val * 10000
        else:
            value = num_val
        wtype = '월급' if '월' in s or '월급' in s else ('시급' if '시' in s or '시급' in s else None)
        return {'wage_type': wtype, 'wage_value_krw': value, 'wage_raw': text}
    return {'wage_type': None, 'wage_value_krw': None, 'wage_raw': text}


def parse_gui_ln(gui: Any) -> Dict[str, Any]:
    if not isinstance(gui, str):
        return {'region': None, 'career': None, 'gui_raw': gui}
    parts = [p.strip() for p in gui.split('/')]
    region = parts[1] if len(parts) >= 2 else None
    career = parts[2] if len(parts) >= 3 else None
    return {'region': region, 'career': career, 'gui_raw': gui}


def clean_dataframe(df: pd.DataFrame, convert_monthly: bool = False, hours_per_month: int = 209) -> pd.DataFrame:
    # Only keep the original fields required for our filtered output and parsing
    keep = [
        'CMPNY_NM', 'JO_SJ', 'HOPE_WAGE', 'GUI_LN',
        'RCRIT_JSSFC_CMMN_CODE_SE', 'JOBCODE_NM', 'CAREER_CND_CMMN_CODE_SE', 'ACDMCR_CMMN_CODE_SE'
    ]
    existing = [c for c in keep if c in df.columns]
    out = df[existing].copy()
    # Minimal renaming: keep only the fields we parse/use
    rename_map = {
        'CMPNY_NM': 'company',
        'JO_SJ': 'job_title',
        'HOPE_WAGE': 'hope_wage',
        'GUI_LN': 'gui_ln'
    }
    out = out.rename(columns=rename_map)

    parsed = out['hope_wage'].fillna('').apply(parse_wage)
    wdf = pd.DataFrame(parsed.tolist(), index=out.index)
    out = pd.concat([out, wdf], axis=1)

    mask = out['wage_value_krw'].isnull()
    if 'gui_ln' in out.columns and mask.any():
        gui_parsed = out.loc[mask, 'gui_ln'].apply(parse_wage)
        out.loc[mask, ['wage_type', 'wage_value_krw', 'wage_raw']] = pd.DataFrame(gui_parsed.tolist(), index=gui_parsed.index)

    gui_info = out['gui_ln'].apply(parse_gui_ln) if 'gui_ln' in out.columns else pd.Series([{'region': None, 'career': None, 'gui_raw': None}] * len(out), index=out.index)
    gdf = pd.DataFrame(gui_info.tolist(), index=out.index)
    out = pd.concat([out, gdf], axis=1)

    # we don't need contact or address information for the filtered output;
    # keep the DataFrame focused on company/title/wage/region/codes

    # Optional: convert 시급 to 월급 by multiplying hours_per_month
    if convert_monthly:
        def to_monthly(row):
            if row.get('wage_type') == '시급' and row.get('wage_value_krw'):
                return int(row['wage_value_krw'] * hours_per_month)
            if row.get('wage_type') == '월급' and row.get('wage_value_krw'):
                return int(row['wage_value_krw'])
            return None
        out['wage_value_monthly'] = out.apply(to_monthly, axis=1)

    return out


def fetch_with_endpoint(session: requests.Session, endpoint: str, record_path: str = '', params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    j = get_json(session, endpoint, params=params)
    records = extract_by_path(j, record_path) if record_path else None
    if records is None and isinstance(j, dict):
        for candidate in ('data', 'result', 'items', 'list'):
            if candidate in j:
                records = j[candidate]
                break
    if records is None and isinstance(j, list):
        records = j
    return ensure_list(records)


def fetch_seoul_by_key(session: requests.Session, key: str, industry: str, chunk_size: int = 100, max_records: Optional[int] = None) -> List[Dict[str, Any]]:
    # GetJobInfo endpoint format: /{key}/json/GetJobInfo/{start}/{end}//{industry}
    all_rec = []
    start = 1
    while True:
        end = start + chunk_size - 1
        url = f"http://openapi.seoul.go.kr:8088/{key}/json/GetJobInfo/{start}/{end}//{industry}"
        print('Requesting', url)
        try:
            j = get_json(session, url)
        except Exception as e:
            print('Failed to fetch chunk:', e, file=sys.stderr)
            break
        recs = extract_by_path(j, 'GetJobInfo.row')
        recs = ensure_list(recs)
        if not recs:
            break
        all_rec.extend(recs)
        if max_records and len(all_rec) >= max_records:
            all_rec = all_rec[:max_records]
            break
        if len(recs) < chunk_size:
            break
        start = end + 1
    return all_rec


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--endpoint', '-e')
    p.add_argument('--output', default='data/seoul_jobs.csv')
    p.add_argument('--record-path', '-p', default='')
    p.add_argument('--key', '-k', help='Seoul OpenAPI key', default=DEFAULT_KEY)
    p.add_argument('--industry', help='industry code for GetJobInfo, e.g. J01302')
    p.add_argument('--chunk-size', type=int, default=100)
    p.add_argument('--max-records', type=int, default=0)
    p.add_argument('--clean-output', default='data/seoul_jobs_clean.csv')
    p.add_argument('--convert-monthly', action='store_true', help='Convert hourly wage to monthly using --hours-per-month')
    p.add_argument('--hours-per-month', type=int, default=209)
    args = p.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    session = build_session()
    records: List[Dict[str, Any]] = []

    if args.endpoint:
        print('Fetching from endpoint...')
        records = fetch_with_endpoint(session, args.endpoint, args.record_path)
    else:
        # key 우선순위: CLI 인수 > 환경변수(DEFAULT_KEY)
        key = args.key or DEFAULT_KEY
        if key and args.industry:
            print('Fetching using key+industry...')
            maxr = args.max_records if args.max_records > 0 else None
            records = fetch_seoul_by_key(session, key, args.industry, chunk_size=args.chunk_size, max_records=maxr)
        else:
            print('Provide either --endpoint or (--key and --industry) or set SEOUL_API_KEY env var')
            sys.exit(1)

    if not records:
        print('No records fetched.')
        sys.exit(1)

    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print('Saved raw CSV to', out_path.resolve(), 'rows=', len(df))

    # cleaning
    clean_df = clean_dataframe(df, convert_monthly=args.convert_monthly, hours_per_month=args.hours_per_month)
    clean_out = Path(args.clean_output)
    clean_out.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(clean_out, index=False, encoding='utf-8-sig')
    print('Saved cleaned CSV to', clean_out.resolve(), 'rows=', len(clean_df))

    # --- create filtered CSV with only the requested columns ---
    filtered_cols = [
        'company', 'job_title', 'wage_type', 'wage_value_krw', 'region', 'career',
        'RCRIT_JSSFC_CMMN_CODE_SE', 'JOBCODE_NM', 'CAREER_CND_CMMN_CODE_SE', 'ACDMCR_CMMN_CODE_SE'
    ]
    # Ensure missing columns exist so selection doesn't fail
    for c in filtered_cols:
        if c not in clean_df.columns:
            clean_df[c] = None

    filtered_df = clean_df[filtered_cols].copy()
    filtered_out = Path('data/seoul_jobs_filtered.csv')
    filtered_out.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(filtered_out, index=False, encoding='utf-8-sig')
    print('Saved filtered CSV to', filtered_out.resolve(), 'rows=', len(filtered_df))


if __name__ == '__main__':
    main()
