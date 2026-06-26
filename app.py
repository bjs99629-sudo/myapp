import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

st.markdown(""⚡"전기차 충전 부하란?⚡
'전기차 충전 부하'는 전기차를 충전할 때 전기 시스템에 가해지는 전기 사용량을 의미합니다. 마치 가정에서 여러 가전제품을 동시에 사용하면 전기가 많이 소모되는 것과 같은 원리입니다.

이 부하는 여러 요인에 따라 달라지는데, 예를 들면 다음과 같습니다:

1️⃣충전 속도: 급속 충전은 완속 충전보다 훨씬 높은 부하를 발생시킵니다.  
2️⃣동시 충전 대수: 여러 대의 전기차가 한꺼번에 충전하면 전체 부하가 크게 증가합니다.  
3️⃣충전 시간대: 전기 사용량이 많은 피크 시간대(예: 저녁)에 충전하면 시스템에 더 큰 부담을 줄 수 있습니다.  
이러한 전기차 충전 부하를 분석하는 것은 전력망의 안정적인 운영과 효율적인 에너지 관리를 위해 매우 중요합니다. 예를 들어, 특정 시간대나 특정 지역에서 부하가 집중되면 정전이 발생할 수도 있기 때문입니다. 따라서 이 데이터를 분석하여 언제, 어디서, 얼마나 많은 전기가 필요한지 파악하고 미래의 전기차 보급에 대비하는 데 활용할 수 있습니다.""")



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
