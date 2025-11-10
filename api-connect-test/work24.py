import requests
import pandas as pd
from datetime import datetime
from xml.etree import ElementTree

# 🔑 공공도서관 정보 Open API 키 설정
API_KEY = "d3a114ce-cf99-47c3-af1a-b61dd509373a" 
BASE_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"