import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# 웹 페이지 제목 설정
st.set_page_config(page_title="캘리포니아 주택 데이터 대시보드", layout="wide")
st.title("🏡 캘리포니아 주택 데이터 분석 대시보드")
st.markdown("코랩에서 분석하던 데이터를 웹 스트림릿 서버에서 시각화하는 대시보드입니다.")

# 데이터 로드 경로 설정 (깃허브 레포지토리에 함께 올릴 파일 이름)
csv_file = 'california_housing_train.csv'

# 파일 존재 여부 확인 후 데이터 로드
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    
    # 1. 데이터프레임 미리보기
    st.subheader("📊 데이터프레임 미리보기")
    st.text("데이터 구조를 확인하기 위한 상위 5개 행입니다.")
    st.dataframe(df.head(), use_container_width=True)
    
    # 화면을 레이아웃 분할하기 (시각화 2개를 양옆으로 배치)
    col1, col2 = st.columns(2)
    
    with col1:
        # 2. Scatter Plot
        st.subheader("📈 소득 수준 vs 주택 가격 중위수")
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.scatter(df['median_income'], df['median_house_value'], alpha=0.5, color='#1f77b4')
        ax1.set_title('Median Income vs Median House Value')
        ax1.set_xlabel('Median Income')
        ax1.set_ylabel('Median House Value')
        ax1.grid(True)
        st.pyplot(fig1)  # plt.show() 대신 사용
        
    with col2:
        # 3. Histogram
        st.subheader("⏳ 주택 연령 중위수 분포")
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.hist(df['housing_median_age'], bins=30, edgecolor='black', color='#ff7f0e')
        ax2.set_title('Distribution of Housing Median Age')
        ax2.set_xlabel('Housing Median Age')
        ax2.set_ylabel('Frequency')
        ax2.grid(True)
        st.pyplot(fig2)  # plt.show() 대신 사용

else:
    st.error(f"🚨 '{csv_file}' 파일을 찾을 수 없습니다. 깃허브 레포지토리에 데이터 파일을 함께 업로드해주세요.")
