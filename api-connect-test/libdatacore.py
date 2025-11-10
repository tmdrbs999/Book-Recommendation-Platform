import requests
import pandas as pd
from datetime import datetime
from xml.etree import ElementTree as ET

# ==============================
# 1️⃣ 데이터 가져오기
# ==============================
def get_library_data(
        auth_key, isbn, region, page_no=1, 
        page_size=10, format_type="xml"):
    """
    특정 ISBN 도서를 소장하고 있는 도서관 정보 조회
    """
    base_url = "http://data4library.kr/api/libSrchByBook"
    params = {
        "authKey": auth_key,
        "isbn": isbn,
        "region": region,
        "pageNo": page_no,
        "pageSize": page_size,
        "format": format_type
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"API 요청 실패: {response.status_code}")
    return response.text


# ==============================
# 2️⃣ 데이터 정제 (XML → DataFrame)
# ==============================
def parse_xml_to_df(xml_data):
    root = ET.fromstring(xml_data)
    libs = []
    for lib in root.findall(".//lib"):
        libs.append({
            "libName": lib.findtext("libName"),
            "tel": lib.findtext("tel"),
            "fax": lib.findtext("fax"),
            "homepage": lib.findtext("homepage"),
            "address": lib.findtext("address"),
            "closed": lib.findtext("closed"),
            "operatingTime": lib.findtext("operatingTime"),
            "bookCount": lib.findtext("bookCount")
        })
    return pd.DataFrame(libs)


# ==============================
# 3️⃣ 컬럼명 / 결측값 정리
# ==============================
def clean_dataframe(df):
    df.columns = [
        "도서관명", "전화번호", "팩스", "홈페이지",
        "주소", "휴관일", "운영시간", "보유도서수"
    ]
    df = df.fillna("정보없음")
    return df


# ==============================
# 4️⃣ 결과 저장
# ==============================
def save_to_csv(df, filename=None):
    if filename is None:
        filename = f"library_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"✅ 결과가 '{filename}' 파일로 저장되었습니다.")


# ==============================
# 5️⃣ 실행 (main)
# ==============================
if __name__ == "__main__":
    AUTH_KEY = "343bf365bd0dfe4d16173a27999ae9e4fe417f89ba41a9d5eed55217295bcf11"
    ISBN = "9791167741028"   
    REGION = 11 #서울              
    PAGE_NO = 1
    PAGE_SIZE = 10

    # 1) 데이터 가져오기
    xml_response = get_library_data(AUTH_KEY, ISBN, REGION, PAGE_NO, PAGE_SIZE)

    # 2) DataFrame 변환
    df_raw = parse_xml_to_df(xml_response)

    # 3) 컬럼명 및 결측값 정리
    df_clean = clean_dataframe(df_raw)

    # 4) CSV 저장
    save_to_csv(df_clean)

    print(df_clean.head())
