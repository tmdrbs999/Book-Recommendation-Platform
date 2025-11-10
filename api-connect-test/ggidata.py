import requests
import pandas as pd


# 🔑 경기데이터드림 OpenAPI 명세서
# 기본인자
API_KEY = "8bc0a3c4b8a6474aa86dff79cf729541"
OUTPUT_TYPE = "json"    # 호출 문서(json, xml)
PAGE_INDEX = 1          # 페이지 위치, 기본값: 1(sample key는 1 고정)
PAGE_SIZE = 50          # 페이지 당 요청 숫자, 기본값: 100(sample key는 5 고정)

# 요청인자(선택)
ENTPRRS_NM = ""         # 기업명 (string)
PBANC_CONT = ""         # 공고명 (string)


# https://openapi.gg.go.kr/OPENAPI명?KEY=인증키값&Type=호출문서종류&pIndex=페이지위치
#   &pSize=페이지당요청수&SIGUN_CD=요청인자
# 예시: https://openapi.gg.go.kr/GGJOBABARECRUSTM?KEY=8bc0a3c4b8a6474aa86dff79cf729541
#   &Type=호출문서종류&pIndex=1&pSize=50&PBANC_CONT=41310

# https://openapi.gg.go.kr/GGJOBABARECRUSTM?KEY=8bc0a3c4b8a6474aa86dff79cf729541&Type=xml&pIndex=&pSize=50


# API 요청
BASE_URL = "https://openapi.gg.go.kr/GGJOBABARECRUSTM"

params = {
    "KEY": API_KEY,         # API 인증키
    "Type": OUTPUT_TYPE,                  # xml 또는 json
    "pIndex": PAGE_INDEX,                     # 페이지 번호
    "pSize": PAGE_SIZE,                     # 페이지당 데이터 수
    # "PBANC_CONT": "기술"              # 공고명 (string)
}

# 실제 요청 URL 확인 (선택 사항)
url_with_params = requests.Request('GET', BASE_URL, params=params).prepare().url
print("요청 URL:", url_with_params)
    
response = requests.get(BASE_URL, params=params)
print(response)

response.encoding = 'utf-8'

data = response.json()

print("--- 📚 검색 결과 요약 ---")

# head 부분 추출
head = data["GGJOBABARECRUSTM"][0]["head"]
total_count = head[0].get("list_total_count")
api_version = head[2].get("api_version")

print(f"총 검색 결과: {total_count}")
print(f"API 버전: {api_version}")

# --- 📖 첫 번째 채용 정보 (출력 테스트) ---
rows = data["GGJOBABARECRUSTM"][1]["row"]

if rows and len(rows) > 0:
    print("\n--- 📖 첫 번째 채용 정보 ---")
    first = rows[1]
    print(f"기업명: {first.get('ENTRPRS_NM')}")
    print(f"공고 내용: {first.get('PBANC_CONT')}")
    print(f"고용형태: {first.get('PBANC_FORM_DIV')}")
    print(f"근무지: {first.get('WORK_REGION_CONT')}")
    print(f"경력: {first.get('CAREER_DIV')}")
    print(f"학력: {first.get('ACDMCR_DIV')}")
    print(f"모집 인원: {first.get('EMPLMNT_PSNCNT')}")
    print(f"접수기간: {first.get('RCPT_BGNG_DE')} ~ {first.get('RCPT_END_DE')}")
    print(f"링크: {first.get('URL')}")
else:
    print("채용 정보가 없습니다.")


# 'row' 부분만 추출 (채용정보 목록)
rows = data["GGJOBABARECRUSTM"][1]["row"]

# DataFrame 변환
df = pd.DataFrame(rows)
df_filtered = df[['ENTRPRS_NM', 'PBANC_CONT', 'SALARY_COND', 'WORK_REGION_CONT', 
                  'CAREER_CD_NM', 'ACDMCR_CD_NM', 'RECRUT_FIELD_CD_NM', 'RECRUT_FIELD_NM', 'URL']]

Index_df_filtered = ['기업명(ENTRPRS_NM)', '공고 내용(PBANC_CONT)', '급여조건(SALARY_COND)', '근무지(WORK_REGION_CONT)', 
                  '경력코드(CAREER_CD_NM)', '학력코드(ACDMCR_CD_NM)', '모집분야코드(RECRUT_FIELD_CD_NM)', '모집분야(RECRUT_FIELD_NM)', 'URL']

# 결과 확인
print(df_filtered.head())

df_filtered.to_csv("ggdata_jobs.csv", index=False, header=Index_df_filtered, encoding="utf-8-sig")
# df_filtered.to_csv("ggdata_jobs.csv", index=False, encoding="utf-8-sig")


