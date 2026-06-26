import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

# 페이지 제목 설정
st.set_page_config(page_title="부하구분 대시보드", layout="wide")
st.title("📊 지역 및 계절별 부하구분명 빈도 분석")

# 1. 데이터 안전하게 로드하기 (인코딩 문제 해결)
@st.cache_data # 데이터를 매번 새로 읽지 않도록 캐싱하여 속도 향상
def load_data():
    encodings = ['utf-8-sig', 'cp949', 'euc-kr']
    for enc in encodings:
        try:
            # 깨진 줄은 건너뛰고 지정된 인코딩으로 읽기 시도
            return pd.read_csv('Electronic Car.csv', on_bad_lines='skip', encoding=enc)
        except (UnicodeDecodeError, TypeError):
            continue
    # 모든 인코딩이 실패했을 때의 예외 처리
    st.error("CSV 파일을 읽을 수 없습니다. 인코딩 형식을 확인해 주세요.")
    return None

df = load_data()

# 데이터가 성공적으로 로드된 경우에만 시각화 진행
if df is not None:
    
    # 주피터의 display(df.head()) 대신 스트림릿 전용 함수 사용 (상위 5개 행 보기)
    st.subheader("📋 데이터 미리보기 (Top 5)")
    st.dataframe(df.head())
    
    st.markdown("---") # 구분선
    
    # 2. 데이터 가공
    combined_counts = df.groupby(['지역구분명', '계절구분명', '부하구분명']).size().reset_index(name='빈도수')

    # 3. 그래프 생성
    grid = sns.catplot(
        data=combined_counts, 
        x='계절구분명', 
        y='빈도수', 
        hue='부하구분명', 
        col='지역구분명', 
        kind='bar', 
        palette='Paired', 
        height=5, 
        aspect=1.2
    )

    # 스타일 및 타이틀 설정
    fig = grid.fig
    fig.suptitle('지역 및 계절별 부하구분명 빈도 비교', y=1.05, fontsize=16)

    # 각 서브플롯(ax)에 그리드 추가
    for ax in grid.axes.flat:
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    # 스트림릿 공간에 그래프 출력
    st.subheader("📈 시각화 결과")
    st.pyplot(fig)
