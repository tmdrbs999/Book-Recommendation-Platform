import requests
import csv
from datetime import datetime
import os

# 책 목록 검색 기본 url
base_url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"

# --- 🔑 사용자 정보 및 검색 조건 설정 ---
TTB_KEY = "ttbsiloam727611326001"
#SEARCH_QUERY = "Database"
MAX_RESULTS = 10
START_PAGE = 1
COVER_TYPE = "Mid"
OUTPUT_TYPE = "JS" 
VERSION = "20131101"




#원본 item 리스트 그대로 가져오기
def fetch_aladin_items(query):
    # Query 파라미터 설정
    params = {
        "ttbkey": TTB_KEY,
        "Query": query,            #찾고 싶은 책 리스트들은 입력값으로 받아온다
        "QueryType": "Title",
        "SearchTarget": "Book",
        "Start": START_PAGE,
        "MaxResults": MAX_RESULTS,
        "Cover": COVER_TYPE,
        "output": OUTPUT_TYPE,
        "Version": VERSION
     
    }
    
    try:
        res = requests.get(base_url, params=params)
        res.raise_for_status()  #요청 실패 시 에러 발생시키기
        
        data = res.json()
        items = data.get("item", [])
        
        return items           
    except Exception as e:
        print("API 호출 중 오류 발생:", e)
        return []

#필요한 필드 골라서 정제하기
def extract_book_fields(items, main_category):
    extracted = []
    
    for it in items:
        book = {
            "title": it.get("title", "").strip(),   #빈 문자열 or None 방지
            "author": it.get("author", "").strip(),
            "categoryId": it.get("categoryId"),
            "mainCategory": main_category,  # 추가로 생성한 카테고리 이름
            "link": it.get("link"),
            "price": it.get("priceSales"),
            "cover": it.get("cover")
        }    
        extracted.append(book)
    
    return extracted

# main_category가 동적으로 넘겨받아 유지보수 쉽게 설계
def fetch_and_extract(query):
    items = fetch_aladin_items(query)   #동적으로 책 리스트 넘기는 부분 
    books = extract_book_fields(items, main_category=query)
    return books

def save_to_csv(books, query):
    if not books:
        print("저장할 책 데이터가 없습니다. CSV 저장을 건너뜁니다.")
        return
    
    #data 폴더가 없다면 자동으로 생성
    os.makedirs("../data", exist_ok=True)
    
    #파일 생성 시간 기준으로 data 폴더에 csv 파일 저장
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"../data/{query}_books_{now}.csv"    
    
    #저장할 필드 이름 (CSV 컬럼 순서)
    fieldnames = ["title", "author", "categoryId", "mainCategory", "price", "link", "cover"]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader() #CSV 헤더
        writer.writerows(books)
        
    print(f"CSV 파일 저장 완료: {filename}")

# 사용 여부에 따라 바뀌어져야 하는 부분
#검색어 목록을 리스트로 관리, env파일에서 불러오기, 사용자 입력 받기, 더 상위 함수에서 호출
#현재는 간단히 사용자 입력
if __name__ == "__main__":
    query = input("찾고 싶은 카테고리를 입력하시오: ")
    books = fetch_and_extract(query)
    save_to_csv(books, query)