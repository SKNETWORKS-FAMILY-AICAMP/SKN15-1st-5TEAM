import pymysql
import pandas as pd
import streamlit as st
import altair as alt
import random
from sk15_team5_crawling import (
    crawl_all_data,
    hyundai_crawling,
    kia_crawling,
    kgm_crawling,
    chevrolet_crawling
)

def generate_unique_random_colors(brand_list):
    #random.seed(42)
    colors = set()
    while len(colors) < len(brand_list):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        colors.add(f"#{r:02x}{g:02x}{b:02x}")
    colors = list(colors)
    random.shuffle(colors)
    return dict(zip(brand_list, colors))


st.sidebar.title("🧠 파이썬쉽조")
page = st.sidebar.radio("이동할 페이지를 선택하세요", ["📊 메인 페이지", "🕸️ 크롤링 페이지"])


conn = pymysql.connect(
    host='192.168.0.22',
    user='team_5',
    password='123',
    database='sk15_5team',
    port=3306,
    charset='utf8'
)

# --------------------- 메인 페이지 ---------------------
if page == "📊 메인 페이지":
    st.title("📈 자동차 판매 데이터 분석")

    # 브랜드 매핑
    def get_brand_id_mapping(conn):
        return pd.read_sql("SELECT BRAND_ID, NAME, COUNTRY FROM BRAND", conn)

    def get_faqs(brand_id, conn):
        query = """
            SELECT b.NAME as 브랜드, f.QUESTION, f.ANSWER
            FROM BRAND_FAQ f
            JOIN BRAND b ON f.BRAND_ID = b.BRAND_ID
            WHERE f.BRAND_ID = %s
        """
        return pd.read_sql(query, conn, params=[brand_id])

    df_brand_id = get_brand_id_mapping(conn)
    df_brand_id['구분'] = df_brand_id['COUNTRY'].apply(lambda x: '국산' if x == 'KOREA' else '외제')

    query = """
    SELECT
        b.NAME AS 브랜드,
        s.YEAR AS 년도,
        s.MONTH AS 월,
        m.NAME AS 모델,
        s.SALES_COUNT AS 판매량
    FROM
        CAR_SALES s
        JOIN CAR_MODEL m ON s.MODEL_ID = m.MODEL_ID
        JOIN BRAND b ON m.BRAND_ID = b.BRAND_ID
    """
    df_all = pd.read_sql(query, conn)
    df_all = df_all.merge(df_brand_id[['NAME', '구분']], left_on='브랜드', right_on='NAME', how='left')

    # 사이드바 필터
    st.sidebar.markdown("---")
    st.sidebar.title("🔍 필터")
    year_list = ['전체'] + sorted(df_all['년도'].unique(), reverse=True)
    month_list = ['전체'] + sorted(df_all['월'].unique())
    brand_list = ['전체'] + sorted(df_all['브랜드'].unique())
    type_list = ['전체', '국산', '외제']

    select_type = st.sidebar.selectbox('국산차/외제차', type_list)
    # 브랜드 리스트 필터링
    if select_type == '전체':
        brand_list = ['전체'] + sorted(df_all['브랜드'].unique())
    else:
        brand_list = ['전체'] + sorted(df_all[df_all['구분'] == select_type]['브랜드'].unique())

    select_brand = st.sidebar.selectbox('회사(브랜드) 선택', brand_list)
    select_year = st.sidebar.selectbox('연도 선택', year_list)
    select_mon = st.sidebar.selectbox('월 선택', month_list)
    brand_list_without_all = [x for x in brand_list if x != '전체']
    brand_color_map = generate_unique_random_colors(brand_list_without_all)

    # 필터링 적용
    fi = df_all.copy()
    if select_year != '전체':
        fi = fi[fi['년도'] == int(select_year)]
    if select_mon != '전체':
        fi = fi[fi['월'] == int(select_mon)]
    if select_type != '전체':
        fi = fi[fi['구분'] == select_type]

    # ---------------- 시각화 ----------------
    # 국산/외제차 전체 가로 바, 파이
    if select_type == '전체' and select_brand == '전체':
        type_sales = fi.groupby('구분')['판매량'].sum().reset_index()
        total_sales = type_sales['판매량'].sum()
        if total_sales > 0:
            type_sales['점유율(%)'] = (type_sales['판매량'] / total_sales * 100).round(2)

            # 바
            chart = alt.Chart(type_sales).mark_bar().encode(
                x=alt.X('판매량:Q', title='판매량'),
                y=alt.Y('구분:N', sort='-x', axis=alt.Axis(labelAngle=0, title='구분')),
                color=alt.Color('구분:N', scale=alt.Scale(
                    domain=['국산', '외제'],
                    range=['#1f77b4', '#ff7f0e']
                )),
                tooltip=['구분:N', '판매량:Q']
            ).properties(
                width=400,
                height=alt.Step(40),
                title=f'국산/외제차 판매량 (연도: {select_year}, 월: {select_mon})'
            )
            st.altair_chart(chart, use_container_width=True)

            # 파이
            chart_pie = alt.Chart(type_sales).mark_arc().encode(
                theta=alt.Theta('점유율(%):Q', stack=True),
                color=alt.Color('구분:N', scale=alt.Scale(
                    domain=['국산', '외제'],
                    range=['#1f77b4', '#ff7f0e']
                )),
                tooltip=['구분:N', alt.Tooltip('점유율(%):Q', title='점유율(%)')]
            ).properties(
                title='국산/외제차 점유율',
                width=400,
                height=400
            )
            st.altair_chart(chart_pie, use_container_width=True)
        else:
            st.warning("해당 조건에 맞는 판매 데이터가 없습니다.")

    # 국산/외제 선택 시: 해당 브랜드별 가로 바, 파이
    elif select_type in ['국산', '외제'] and select_brand == '전체':
        brand_sales = fi.groupby('브랜드')['판매량'].sum().reset_index()
        total_sales = brand_sales['판매량'].sum()
        if total_sales > 0:
            brand_sales['점유율(%)'] = (brand_sales['판매량'] / total_sales * 100).round(2)

            # 바
            chart = alt.Chart(brand_sales).mark_bar().encode(
                x=alt.X('판매량:Q', title='판매량'),
                y=alt.Y('브랜드:N', sort='-x', axis=alt.Axis(labelAngle=0, title='브랜드')),
                color=alt.Color('브랜드:N', scale=alt.Scale(
                    domain=brand_sales['브랜드'].unique(),
                    range=[brand_color_map.get(b, '#888888') for b in brand_sales['브랜드'].unique()]
                ), legend=None),
                tooltip=['브랜드:N', '판매량:Q']
            ).properties(
                width=700,
                height=alt.Step(40),
                title=f'{select_type} 브랜드별 판매량 (연도: {select_year}, 월: {select_mon})'
            )
            st.altair_chart(chart, use_container_width=True)

            # 파이
            chart_pie = alt.Chart(brand_sales).mark_arc().encode(
                theta=alt.Theta('점유율(%):Q', stack=True),
                color=alt.Color('브랜드:N', scale=alt.Scale(
                    domain=brand_sales['브랜드'].unique(),
                    range=[brand_color_map.get(b, '#888888') for b in brand_sales['브랜드'].unique()]
                ), legend=alt.Legend(title="브랜드")),
                tooltip=['브랜드:N', alt.Tooltip('점유율(%):Q', title='점유율(%)')]
            ).properties(
                title=f'{select_type} 브랜드별 점유율 (파이차트)',
                width=400,
                height=400
            )
            st.altair_chart(chart_pie, use_container_width=True)
        else:
            st.warning("해당 조건에 맞는 판매 데이터가 없습니다.")

    # 특정 브랜드 선택 시: 모델별 바, 파이
    elif select_brand != '전체':
        brand_fi = fi[fi['브랜드'] == select_brand]
        model_sales = brand_fi.groupby('모델')['판매량'].sum().reset_index()
        model_total = model_sales['판매량'].sum()
        if model_total > 0:
            model_sales['점유율(%)'] = (model_sales['판매량'] / model_total * 100).round(2)

            # 바
            chart = alt.Chart(model_sales).mark_bar().encode(
                x=alt.X('판매량:Q', title='판매량'),
                y=alt.Y('모델:N', sort='-x', axis=alt.Axis(labelAngle=0, labelLimit=400, labelFontSize=14, labelPadding=15), title='모델'),
                color=alt.Color('모델:N', legend=None),
                tooltip=['모델:N', '판매량:Q']
            ).properties(
                width=700,
                height=alt.Step(40),
                title=f'{select_brand} 모델별 판매량 (연도: {select_year}, 월: {select_mon})'
            )
            st.altair_chart(chart, use_container_width=True)

            # 파이
            chart_pie = alt.Chart(model_sales).mark_arc().encode(
                theta=alt.Theta('점유율(%):Q', stack=True),
                color=alt.Color('모델:N', legend=alt.Legend(title="모델")),
                tooltip=['모델:N', alt.Tooltip('점유율(%):Q', title='점유율(%)')]
            ).properties(
                title=f'{select_brand} 모델별 점유율',
                width=400,
                height=400
            )
            st.altair_chart(chart_pie, use_container_width=True)

            # FAQ 표시
            brand_id = df_brand_id.loc[df_brand_id['NAME'] == select_brand, 'BRAND_ID'].iloc[0]
            df_faq = get_faqs(brand_id, conn)

            st.markdown("---")
            st.header("FAQ")

            if not df_faq.empty:
                for _, row in df_faq.iterrows():
                    st.markdown(f"**질문:** {row['QUESTION']}")
                    st.markdown(f"**답변:** {row['ANSWER']}")
                    st.markdown("---")
            else:
                st.write("FAQ가 없습니다.")
        else:
            st.warning("해당 브랜드에 대한 판매 데이터가 없습니다.")
# --------------------- 크롤링 페이지 ---------------------
elif page == "🕸️ 크롤링 페이지":

    st.title("🕷️ 자동차 데이터 크롤링 페이지")
    st.markdown("각 버튼을 눌러 데이터를 수집하세요.")

    if st.button("🚘 국산 자동차 판매 데이터 전체 크롤링"):
        with st.spinner("자동차 판매 데이터를 수집 중입니다..."):
            try:
                crawl_all_data('국산')
                st.success("자동차 판매 데이터 수집 완료!")
            except Exception as e:
                st.error(f"자동차 데이터 크롤링 실패: {e}")

    if st.button("🚘 외제 자동차 판매 데이터 전체 크롤링"):
        with st.spinner("자동차 판매 데이터를 수집 중입니다..."):
            try:
                crawl_all_data('외제')
                st.success("자동차 판매 데이터 수집 완료!")
            except Exception as e:
                st.error(f"자동차 데이터 크롤링 실패: {e}")

    if st.button("❓ FAQ 크롤링 - HYUNDAI"):
        with st.spinner("현대 FAQ 수집 중..."):
            try:
                hyundai_crawling()
                st.success("현대 FAQ 수집 완료!")
            except Exception as e:
                st.error(f"현대 FAQ 크롤링 실패: {e}")

    if st.button("❓ FAQ 크롤링 - KIA"):
        with st.spinner("기아 FAQ 수집 중..."):
            try:
                kia_crawling()
                st.success("기아 FAQ 수집 완료!")
            except Exception as e:
                st.error(f"기아 FAQ 크롤링 실패: {e}")

    if st.button("❓ FAQ 크롤링 - KGM"):
        with st.spinner("KGM FAQ 수집 중..."):
            try:
                kgm_crawling()
                st.success("KGM FAQ 수집 완료!")
            except Exception as e:
                st.error(f"KGM FAQ 크롤링 실패: {e}")

    if st.button("❓ FAQ 크롤링 - CHEVROLET"):
        with st.spinner("쉐보레 FAQ 수집 중..."):
            try:
                chevrolet_crawling()
                st.success("쉐보레 FAQ 수집 완료!")
            except Exception as e:
                st.error(f"쉐보레 FAQ 크롤링 실패: {e}")


# 연결 종료
conn.close()
