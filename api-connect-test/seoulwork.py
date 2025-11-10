import requests
import pandas as pd
from datetime import datetime
from xml.etree import ElementTree

# 🔑 공공도서관 정보 Open API 설정
API_KEY = "343bf365bd0dfe4d16173a27999ae9e4fe417f89ba41a9d5eed55217295bcf11" 
BASE_URL = "http://openapi.seoul.go.kr:8088/(인증키)/xml/GetJobInfo/1/5/ / / / /"

# 📡 1) API에서 데이터 가져오기
def fetch_libraries(page_no=1, page_size=10):
    params = {
        "authKey": API_KEY,
        "pageNo": page_no,
        "pageSize": page_size,
        "format": "xml"
    }

    response = requests.get(BASE_URL, params=params)
    response.encoding = "utf-8"

    if response.status_code != 200:
        raise Exception(f"API 요청 실패: {response.status_code}")

    # --- XML 파싱 ---
    root = ElementTree.fromstring(response.text)
    records = []

    # <libs> 하위의 <lib> 태그 반복
    for lib in root.findall(".//lib"):
        record = {child.tag: (child.text or "").strip() for child in lib}
        records.append(record)

    return pd.DataFrame(records)

# 🧹 2) 데이터 정제
def clean_libraries(df):
    if df.empty:
        print("⚠️ 도서관 데이터가 없습니다.")
        return df

    # 컬럼명/결측값 정리
    df = df.drop_duplicates(subset=["libCode"], keep="first")
    df["libName"] = df["libName"].astype(str).str.replace(r"[^가-힣a-zA-Z0-9 ]", "", regex=True)
    df["address"] = df["address"].astype(str).str.strip()
    df["tel"] = df["tel"].fillna("정보없음")
    df["homepage"] = df["homepage"].fillna("정보없음")

    return df

# 💾 3) 결과 저장
def save_to_csv(df):
    filename = f"libraries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"✅ 도서관 정보 저장 완료: {filename}")


# 🚀 실행
if __name__ == "__main__":
    print("📡 공공도서관 API에서 데이터 수집 중...")

    try:
        df = fetch_libraries(page_no=1, page_size=10)
        print(f"📚 {len(df)}개의 도서관 정보 수집 완료")

        print("🧹 데이터 정제 중...")
        df = clean_libraries(df)

        save_to_csv(df)

    except requests.exceptions.RequestException as e:
        print(f"🌐 네트워크 오류 발생: {e}")
    except ElementTree.ParseError:
        print("❌ XML 파싱 오류 발생 — 응답 형식을 확인하세요.")
    except Exception as e:
        print(f"⚠️ 처리 중 오류 발생: {e}")
