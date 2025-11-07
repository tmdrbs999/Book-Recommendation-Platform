import requests
import xmltodict
import json

# --- 🔑 사용자 정보 및 검색 조건 설정 ---
# **[필수] 발급받은 인증키로 변경하세요!**
AUTH_KEY = "343bf365bd0dfe4d16173a27999ae9e4fe417f89ba41a9d5eed55217295bcf11" 
PAGE_NO = 1       # 페이지 번호
PAGE_SIZE = 2    # 페이지 크기 (기본값 10)
# LIB_CODE = 111001 # 특정 도서관 코드를 지정할 경우 (선택)

# --- 🌐 API 요청 URL 및 파라미터 설정 ---
BASE_URL = "http://data4library.kr/api/libSrch"

# 파라미터 딕셔너리
params = {
    "authKey": AUTH_KEY,
    "pageNo": PAGE_NO,
    "pageSize": PAGE_SIZE,
    # format 파라미터가 없으면 기본적으로 XML 응답 (format="xml"과 동일)
    # "format": "xml" 
}

# --- 🚀 API 호출 함수 ---
def fetch_library_info():
    try:
        # API 호출
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # HTTP 오류(4xx, 5xx) 발생 시 예외 처리

        xml_data = response.text
        
        # 🚨 디버깅: XML 파싱 시도 전에 응답 내용을 출력하여 확인
        print("\n--- 🚧 API 응답 내용 확인 (디버깅) ---")
        print(xml_data[:500]) # 응답 내용의 처음 500자만 출력
        print("-------------------------------------------\n")

        # XML을 Python 딕셔너리로 변환합니다.
        data = xmltodict.parse(xml_data)
        
        # --- 📚 데이터 추출 (이후 코드는 동일) ---
        response_data = data.get('response', {})
        libs_data = response_data.get('libs', {})
        
        num_found = response_data.get('numFound', 'N/A')
        
        print("--- 🏢 도서관 정보 검색 결과 ---")
        print(f"✅ 전체 검색 결과 건수: {num_found}건")
        
        # ... (이하 코드는 이전과 동일) ...
        # ...
        
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 네트워크 오류 발생: {e}")
    except xmltodict.expat.ExpatError:
        print("❌ API 응답을 XML로 파싱하는 데 실패했습니다. (응답 내용이 올바른 XML 형식이 아닐 수 있습니다.)")
        # 실패 시 원본 응답 내용을 다시 출력하여 확인
        if 'xml_data' in locals():
             print("\n🚨 파싱 실패 응답 원본 (다시 확인):")
             print(xml_data[:500]) # 오류를 일으킨 응답을 다시 출력
    except Exception as e:
        print(f"처리 중 예상치 못한 오류 발생: {e}")

# 함수 실행
fetch_library_info()