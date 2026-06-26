import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

# 페이지 제목 설정
st.set_page_config(page_title="부하구분 대시보드", layout="wide")
st.title("📊 지역 및 계절별 부하구분명 빈도 분석")

# [주의] 가상의 df 데이터 로드 예시 (실제 데이터 로드 코드로 대체하세요)
# df = pd.read_csv('your_data.csv') 

# 1. 데이터 가공
combined_counts = df.groupby(['지역구분명', '계절구분명', '부하구분명']).size().reset_index(name='빈도수')

# 2. 그래프 생성 (plt.figure 대신 sns.catplot의 결과물 활용)
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

# catplot은 자체 figure를 가지므로 grid.fig로 접근하여 스타일 수정
fig = grid.fig
fig.suptitle('지역 및 계절별 부하구분명 빈도 비교', y=1.05, fontsize=16)

# 각 서브플롯(ax)에 그리드 추가
for ax in grid.axes.flat:
    ax.grid(axis='y', linestyle='--', alpha=0.7)

# 스트림릿 공간에 그래프 출력
st.pyplot(fig)
