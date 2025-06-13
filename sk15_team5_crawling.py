import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pymysql
import time
import requests
import pandas as pd
import re

# 차량 정보 수집 함수
def get_info(brand, month, driver, conn, cursor):
    time.sleep(1)
    driver.get(f"https://auto.danawa.com/newcar/?Work=record&Tab=Grand&Brand={brand}&Month={month}")
    bs = BeautifulSoup(driver.page_source)
    
    try:
        # 연도 파싱
        select_year = bs.find("select", id='selMonth').select_one("option[selected]")['value']
        # 월 파싱
        selDay = bs.find("select", id='selDay').select_one("option[selected]")['value'].replace("0", "")
    except Exception as e:
        print(f"[{brand}][{month}] 날짜 파싱 오류: {e}")
        return

    for row in bs.find("table", class_="recordTable model").find_all(lambda tag: tag.name == "tr" and not tag.has_attr("class"))[1:]:
        try:
            model_id = row.find("button", class_="viewGraph")['val']
            model_name = row.find("td", class_="title").text.strip()
            sales_count = row.find("td", class_="num").text.strip().replace("그래프로 보기", "").replace(",", "")
            rate_right = row.find("td", class_="rate right").text.strip().replace("%", "")

            # 차량 모델 저장
            try:
                cursor.execute(
                    "INSERT INTO CAR_MODEL(MODEL_ID, BRAND_ID, NAME) VALUES(%s, %s, %s)",
                    [model_id, brand, model_name]
                )
            except Exception as e:
                print(f"모델 INSERT 오류: {e}")

            # 차량별 판매량/점유율 저장
            try:
                cursor.execute(
                    "INSERT INTO CAR_SALES(MODEL_ID, YEAR, MONTH, SALES_COUNT, RATE_RIGHT) VALUES(%s, %s, %s, %s, %s)",
                    [model_id, select_year, selDay, sales_count, rate_right]
                )
            except Exception as e:
                print(f"판매 INSERT 오류: {e}")

            conn.commit()
        except Exception as e:
            print(f"모델 파싱 오류: {e}")

# 전체 크롤링 함수
def crawl_all_data(option):
    
    options = Options()
    options.add_argument('--headless')  # 브라우저 창 없이 실행

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get("https://auto.danawa.com/newcar/?Work=record&Tab=Grand&Brand=303&Month=2025-01-00")
    bs = BeautifulSoup(driver.page_source)

    brand_ids = []
    brand_nms = []
    if option == '국산':
        # 국내 브랜드
        brand_ids = [x['data-brand'] for x in bs.find("div", class_="domestic").find_all("li")]
        brand_nms = [x.find("span", class_="name").text for x in bs.find("div", class_="domestic").find_all("li")]
    elif option == '외제':
        # 해외 브랜드
        brand_ids = [x['data-brand'] for x in bs.find("div", class_="import").find_all("li")]
        brand_nms = [x.find("span", class_="name").text for x in bs.find("div", class_="import").find_all("li")]
    
    
    years = [opt['value'] for opt in bs.find("select", id='selMonth').find_all("option")]
    months = [opt['value'] for opt in bs.find("select", id='selDay').find_all("option")]
    
    for brand in range(6, len(brand_ids)):  # 필요한 범위만
        try:
            conn = pymysql.connect(host='192.168.0.22', user='team_5', passwd='123', database='sk15_5team', port=3306)
            cursor = conn.cursor()

            # 브랜드 등록
            try:
                cursor.execute("INSERT INTO BRAND(BRAND_ID, NAME, COUNTRY) VALUES(%s, %s, %s)", [brand_ids[brand], brand_nms[brand], 'FOREIGN'])
                conn.commit()
            except Exception as e:
                print(f"브랜드 INSERT 오류: {e}")

            # 연도별 월별 수집
            for year in years:
                for month in months:
                    try:
                        crawl_month = f"{year}-{month}-00"
                        get_info(brand_ids[brand], crawl_month, driver, conn, cursor)
                    except Exception as e:
                        print(f"get_info 호출 오류: {e}")
        except Exception as e:
            print(f"DB 연결 오류: {e}")

# FAQ 크롤링 - HYUNDAI
def hyundai_crawling():
    # 실제 API 엔드포인트
    url = 'https://www.hyundai.com/kr/ko/gw/customer-support/v1/customer-support/faq/list'

    # 요청 본문
    payload = {
        "siteTypeCode": "H",
        "faqCategoryCode": "01",  # "일반" 카테고리
        "faqCode": "",
        "faqSeq": "",
        "searchKeyword": "",
        "pageNo": "1",
        "pageSize": "5",
        "externalYn": ""
    }

    # 요청 헤더
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.hyundai.com",
        "referer": "https://www.hyundai.com/kr/ko/e/customer/center/faq",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    # POST 요청
    response = requests.post(url, headers=headers, json=payload)

    # JSON 파싱
    data = response.json()

    # 질문/답변 추출
    faq_list = data['data']['list'] 
    questions = [item['faqQuestion'].strip() for item in faq_list]
    answers = [item['faqAnswer'].strip() for item in faq_list]
    faq_dict = dict(zip(questions, answers))
    # 보기 좋게 데이터프레임 구성
    cleaned_faq_dict = {}
    for q, a in faq_dict.items():
        soup = BeautifulSoup(a, 'html.parser')
        text = soup.get_text(separator=" ", strip=True)
        text = text.replace('\xa0', ' ').replace('&gt;', '>')  # 특수문자 정리
        text = ' '.join(text.split())  # 공백 정리
        cleaned_faq_dict[q] = text

    # 결과 확인
    print(cleaned_faq_dict)
    
    conn = pymysql.connect(host= '192.168.0.22', user= 'play', passwd='123', database='sk15_5team', port= 3306)
    cur = conn.cursor()
    sql = "INSERT INTO BRAND_FAQ (BRAND_ID, QUESTION, ANSWER) VALUES (%s, %s, %s)"

    for idx, (q, a) in enumerate(cleaned_faq_dict.items(), start=1):
        cur.execute(sql, ('303', q, a))  # 각 row를 튜플로 전달

    conn.commit()
    conn.close()
    # 저장 원할 경우:
    # df.to_csv('hyundai_faq.csv', index=False, encoding='utf-8-sig')


# FAQ 크롤링 - KIA
def kia_crawling():
    # 크롬 드라이버 설정
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 없이 실행하고 싶을 경우
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # URL 접속
    driver.get("https://www.kia.com/kr/customer-service/center/faq")
    time.sleep(2)

    question = []
    answer = []

    # 10개 항목 수집
    for q in range(10):
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 질문 텍스트 추출
        q_tag = soup.find("button", id=f"accordion-item-{q}-button")
        if not q_tag:
            question.append("")
            answer.append("")
            continue
        q_text = q_tag.find("span", class_="cmp-accordion__title").text.strip()
        question.append(q_text)

        # 패널을 열기 위해 클릭
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, f"accordion-item-{q}-button"))
        time.sleep(1)  # 클릭 후 내용이 렌더링되길 기다림

        # 다시 파싱 후 내용 추출
        soup = BeautifulSoup(driver.page_source, "html.parser")
        a_div = soup.find("div", id=f"accordion-item-{q}-panel")
        if a_div:
            content_div = a_div.find("div", id="container-619af8ccc1")
            if content_div:
                raw_text = content_div.get_text(separator="\n")
                cleaned = raw_text.replace('\xa0', ' ').strip()
                cleaned = re.sub(r'[ \t]+', ' ', cleaned)
                cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
                cleaned = '\n'.join([line.strip() for line in cleaned.splitlines()])
                answer.append(cleaned)
            else:
                answer.append("")
        else:
            answer.append("")

    df = pd.DataFrame({
        "Question": question,
        "Answer": answer
    })
    faq_dict = dict(zip(question, answer))
    print(faq_dict)
    driver.quit()

    conn = pymysql.connect(host= '', user= '', passwd='', database='sk15_5team', port= 3306)
    cur = conn.cursor()
    sql = "INSERT INTO BRAND_FAQ (BRAND_ID, QUESTION, ANSWER) VALUES (%s, %s, %s)"

    for idx, (q, a) in enumerate(faq_dict.items(), start=1):
        cur.execute(sql, ('307', q, a))  # 각 row를 튜플로 전달

    conn.commit()
    conn.close()

# FAQ 크롤링 - KGM
def kgm_crawling():
    url = "https://web.kg-mobility.com/app/customer/getFaqBestContentList.do?pageIdx=1&rowsPerPage=10"

    payload = {
        'pageIdx' : '1',
        'rowsPerPage' : '10'
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Origin": "https://www.kg-mobility.com",
        "Referer": "https://www.kg-mobility.com/",
        "Host": "web.kg-mobility.com"
    }

    re = requests.get(url, data= payload, headers= headers).json()

    faq_list = re['body']['list']
    titles = [item['title'] for item in faq_list]

# FAQ 크롤링 - CHEVROLET
def chevrolet_crawling():
    title_list = []
    answers_list = []

    # 쉐보레 FAQ URL (한국)
    url = "https://www.chevrolet.co.kr/faq.html"

    # User-Agent 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
    }

    # 페이지 요청
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")


    title = soup.find_all('h6', class_="q-button-text q-headline-text")
    for x in title:
        title_list.append(x.text)
    title_list

    answers = soup.find_all('div', class_ ="q-text q-body1 q-invert")
    for x in answers:
        answers_list.append(x.text.strip())

    faq_dict = dict(zip(title_list, answers_list))
    conn = pymysql.connect(host= '192.168.0.22', user= 'play', passwd='123', database='sk15_5team', port= 3306)
    cur = conn.cursor()
    sql = "INSERT INTO BRAND_FAQ (BRAND_ID, QUESTION, ANSWER) VALUES (%s, %s, %s)"

    for idx, (q, a) in enumerate(faq_dict.items(), start=1):
        cur.execute(sql, ('312', q, a))  # 각 row를 튜플로 전달

    conn.commit()
    conn.close()


#crawl_all_data()
