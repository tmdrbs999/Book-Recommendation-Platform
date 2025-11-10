import requests
import urllib.parse
import json

# --- 🔑 사용자 정보 및 검색 조건 설정 ---
# **[필수] 발급받은 TTBKey로 변경하세요!**
TTB_KEY = "ttbsu888888881532001" 
SEARCH_QUERY = "개발자" # 검색어
MAX_RESULTS = 10
START_PAGE = 1
OUTPUT_TYPE = "JS" # JSON 형식을 요청 (알라딘 API에서는 'JS')
VERSION = "20131101"

# --- 🌐 API 요청 URL 생성 ---
BASE_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"

# Python의 requests 라이브러리는 딕셔너리를 사용하여 URL 인코딩을 자동으로 처리합니다.
params = {
    "ttbkey": TTB_KEY,
    "Query": SEARCH_QUERY,
    "QueryType": "Title",
    "MaxResults": MAX_RESULTS,
    "start": START_PAGE,
    "SearchTarget": "Book",
    "output": OUTPUT_TYPE,
    "Version": VERSION
}

# 실제 요청 URL 확인 (선택 사항)
# url_with_params = requests.Request('GET', BASE_URL, params=params).prepare().url
# print("요청 URL:", url_with_params)

# --- 🚀 API 호출 함수 ---
def fetch_aladin_items():
    try:
        # API 호출
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생

        # JSON 응답 데이터 파싱
        # Aladin API는 output=JS로 요청 시 순수한 JSON 객체를 반환하는 경우가 많습니다.
        data = response.json()
        
        print("--- 📚 검색 결과 요약 ---")
        # 'totalResults'나 'itemsPerPage' 키가 있는지 확인하고 출력합니다.
        print(f"총 검색 결과: {data.get('totalResults')}")
        print(f"페이지 당 개수: {data.get('itemsPerPage')}")
        
        # 첫 번째 상품 정보 출력 예시
        items = data.get('item')
        if items and len(items) > 0:
            print("\n--- 📖 첫 번째 상품 정보 ---")
            first_item = items[0]
            print(f"제목: {first_item.get('title')}")
            print(f"저자: {first_item.get('author')}")
            print(f"출간일: {first_item.get('pubDate')}")
            print(f"가격: {first_item.get('priceStandard')}원")
            print(f"링크: {first_item.get('link')}")
            
            
        else:
            print("검색 결과가 없거나 TTBKey가 유효하지 않습니다.")
            # 오류 발생 시 전체 응답 데이터를 출력하여 문제 파악에 도움을 줄 수 있습니다.
            # print("전체 응답 데이터:", data)

    except requests.exceptions.HTTPError as e:
        print(f"API 호출 중 HTTP 오류 발생: {e}")
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 네트워크 오류 발생: {e}")
    except json.JSONDecodeError:
        print("API 응답을 JSON으로 디코딩하는 데 실패했습니다. (응답이 JSON 형식이 아닐 수 있습니다.)")
        print("응답 내용:", response.text)


# 함수 실행
fetch_aladin_items()