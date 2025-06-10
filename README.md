# SKN15-1st-5TEAM

# 1. 팀 소개

파이썬쉽조😎

노건우 @asdg441  스트림릿 페이지 구현

박진우 @pjw876  자동차판매데이터 크롤링, 데이터베이스 설계, 자료취합 

이세진 @isjini  데이터 검증, 화면구성

임경원 @KYUNGWON-99 FAQ 크롤링

홍민식 @minnnsik FAQ 크롤링


# 2. 프로젝트 개요

🚗자동차 판매 데이터 분석 🚗

👌브랜드 별 판매실적 데이터를 시각화 및 FAQ소개 
- 프로젝트 필요성(배경)


- 프로젝트 목표

 

# 3. 기술 스택
1.프로그래밍 언어

Python

데이터 처리, 차트 생성, 웹 대시보드(예: Streamlit) 구현에 사용됨.

2.프레임워크 및 라이브러리

Streamlit

Python 기반의 웹 대시보드 프레임워크로, 데이터 시각화와 UI를 빠르게 구현할 수 있음.

Altair

Python용 데이터 시각화 라이브러리로 바차트·파이차트 등 다양한 그래프를 쉽게 그릴 수 있음.


3.데이터베이스

MySQL

차량, 브랜드, 판매 데이터 등 구조화된 데이터를 저장하고 조회하는 데 사용됨.

4.서버 환경

Windows


5.개발 도구

Git
MySQL 
VSCode 
 

# 4. 요구사항 명세서
데이터베이스 설계문서(ERD 등)
수집 데이터(크롤링 데이터 등)
데이터 조회 프로그램(소스코드)

# 5. ERD


 ![image](https://github.com/user-attachments/assets/1dbe72e4-7699-4154-a348-26c801eeff07)


# 6. 주요 프로시저
1. 데이터 수집 (크롤링)
⛏ 프로시저 목록:
crawl_all_data():
목적: CAR_MODEL, CAR_SALES, BRAND 테이블에 국내외 브랜드의 월별 판매 데이터를 저장
흐름: 브랜드 → 연도 → 월별 반복 → get_info() 호출

get_info(brand, month, driver, conn, cursor):
목적: 브랜드의 특정 월 차량 모델 및 판매 데이터 추출 → DB 저장

hyundai_crawling(), kia_crawling(), kgm_crawling(), chevrolet_crawling():
목적: 각 브랜드의 공식 FAQ 페이지에서 질문/답변 추출 → BRAND_FAQ 테이블에 저장

2. 데이터 저장 (MySQL)
⛏ 대상 테이블:
BRAND: 브랜드 정보 (ID, 이름, 국산/외제 구분)
CAR_MODEL: 차량 모델 정보 (모델 ID, 브랜드 ID, 모델 이름)
CAR_SALES: 연도별 모델 판매량 및 점유율
BRAND_FAQ: 브랜드별 FAQ (질문, 답변)

🔒 저장 처리 방식:
INSERT ... ON DUPLICATE KEY UPDATE 또는 예외 무시 방식 (try-except)으로 중복 방지
커넥션 유지 및 커밋 (conn.commit())

3. 데이터 시각화 및 조회 (메인 페이지)
⛏ 프로시저 목록:
필터링 (연도, 월, 브랜드, 국산/외제 구분)
판매량 기준 Bar Chart, Pie Chart 시각화
선택 브랜드 FAQ 동시 출력

4. Streamlit UI 흐름
⛏ 페이지 구성:
사이드바: 필터/페이지 전환
메인 페이지 (📊 메인 페이지)
필터 선택 → 판매 데이터 시각화 → 브랜드 FAQ 출력
크롤링 페이지 (🕸️ 크롤링 페이지)
버튼 클릭 → 각 크롤링 함수 실행 → 데이터 저장 → 완료 메시지 출력

# 7. 수행결과(테스트/시연 페이지)

 

# 8. 한 줄 회고
