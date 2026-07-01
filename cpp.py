import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ----------------------------------------------------
# 1. 페이지 기본 설정 및 테마 적용
# ----------------------------------------------------
st.set_page_config(
    page_title="스마트 출석체크 시스템",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS 주입으로 프리미엄 UI 디자인 구현
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
    
    /* 폰트 및 배경 스타일 */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    /* 타이틀 그라디언트 */
    .main-title {
        background: linear-gradient(135deg, #A88BEB 0%, #F1A7F1 50%, #FFCAD4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        color: #A0A0B0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 커스텀 카드 스타일 */
    .metric-card {
        background: rgba(30, 30, 47, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(108, 92, 231, 0.5);
        box-shadow: 0 12px 40px 0 rgba(108, 92, 231, 0.15);
    }
    
    /* 상태 표시 배지 */
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 10rem;
    }
    .badge-present { background-color: #2ecc71; color: white; }
    .badge-late { background-color: #f1c40f; color: black; }
    
    /* 폼 컨테이너 */
    .form-container {
        background: #1E1E2F;
        border-radius: 20px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 데이터베이스 연동 및 폴백 설정
# ----------------------------------------------------
DB_FILE = "attendance_db.csv"
SETTINGS_FILE = "settings.csv"

# 세션 상태 초기화 (관리자 기준 시간 등)
if "cutoff_time" not in st.session_state:
    st.session_state.cutoff_time = "09:00"
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin" # 기본 비밀번호

# 설정 로드 함수
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            settings_df = pd.read_csv(SETTINGS_FILE)
            if not settings_df.empty:
                st.session_state.cutoff_time = settings_df.loc[0, "cutoff_time"]
                st.session_state.admin_password = str(settings_df.loc[0, "admin_password"])
        except Exception:
            pass

def save_settings(cutoff_time, password):
    settings_df = pd.DataFrame([{"cutoff_time": cutoff_time, "admin_password": password}])
    settings_df.to_csv(SETTINGS_FILE, index=False)
    st.session_state.cutoff_time = cutoff_time
    st.session_state.admin_password = password

load_settings()

# 구글 스프레드시트 정보가 secrets에 설정되어 있는지 확인
conn_configured = False
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    conn_configured = True

# 데이터 읽기 함수
def get_attendance_data():
    if conn_configured:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # st.cache_data를 사용하지 않고 매번 최신 데이터를 읽어옴
            df = conn.read(ttl="0d")
            # 컬럼 정규화
            df.columns = [col.strip() for col in df.columns]
            return df
        except Exception as e:
            st.sidebar.warning(f"구글 시트 로드 중 에러 발생, 로컬 DB로 임시 전환됩니다. ({e})")
            
    # Fallback: 로컬 CSV 파일 사용
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["날짜", "이름", "체크인 시간", "상태", "비고"])

# 데이터 추가 함수
def add_attendance_record(date_str, name, check_in_time, status, notes):
    new_record = {
        "날짜": date_str,
        "이름": name,
        "체크인 시간": check_in_time,
        "상태": status,
        "비고": notes
    }
    
    if conn_configured:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # 현재 데이터 가져옴
            df = get_attendance_data()
            # 데이터 추가
            new_df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            # 구글 시트에 업데이트
            conn.update(data=new_df)
            return True
        except Exception as e:
            st.error(f"구글 시트 저장 실패: {e}. 로컬에 데이터를 저장합니다.")
            
    # 로컬 저장 Fallback
    df = get_attendance_data()
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    return True

# 데이터 중복 출석 검사
def is_already_checked_in(date_str, name):
    df = get_attendance_data()
    if df.empty:
        return False
    return not df[(df["날짜"] == date_str) & (df["이름"] == name)].empty

# ----------------------------------------------------
# 3. 사이드바 - 연결 상태 및 도움말
# ----------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/checked-laptop.png", width=120)
    st.markdown("### 📅 스마트 출석체크")
    st.markdown("---")
    
    if conn_configured:
        st.success("🟢 Google Sheets 연동 완료")
    else:
        st.info("🟡 로컬 파일 모드 작동 중")
        
    st.markdown("---")
    st.caption("v1.0.0 | Created by Antigravity")

# ----------------------------------------------------
# 4. 메인 화면 헤더
# ----------------------------------------------------
st.markdown('<div class="main-title">스마트 출석체크 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">구글 스프레드시트 연동 기반의 출석 기록 및 대시보드 시스템</div>', unsafe_allow_html=True)

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 출석 체크", "📊 통계 대시보드", "⚙️ 관리 콘솔"])

# ----------------------------------------------------
# TAB 1: 출석 체크
# ----------------------------------------------------
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("출석 정보 입력")
        
        with st.form("check_in_form", clear_on_submit=True):
            name = st.text_input("👤 이름 / ID", placeholder="본인의 이름을 입력하세요", max_chars=20)
            
            # 날짜 및 시간 입력 (기본값: 현재 시간)
            now = datetime.datetime.now()
            selected_date = st.date_input("📅 날짜 선택", value=now.date())
            
            # 시간 선택 (직관적인 드롭다운 선택 및 직접 검색 가능)
            st.markdown("<div style='margin-top: 10px; margin-bottom: 5px;'><label style='font-size: 0.9rem; color: #E0E0E6;'>⏰ 시간 선택 (시 / 분)</label></div>", unsafe_allow_html=True)
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                hours_options = [f"{i:02d}" for i in range(24)]
                selected_hour = st.selectbox("시", options=hours_options, index=now.hour, label_visibility="collapsed")
            with t_col2:
                minutes_options = [f"{i:02d}" for i in range(60)]
                selected_minute = st.selectbox("분", options=minutes_options, index=now.minute, label_visibility="collapsed")
            
            notes = st.text_input("💬 비고 (사유 및 특이사항)", placeholder="지각 사유 등 남기실 말씀이 있다면 작성하세요")
            
            submit_btn = st.form_submit_button("🚀 출석 완료")
            
            if submit_btn:
                if not name.strip():
                    st.error("이름을 입력해주세요.")
                else:
                    date_str = selected_date.strftime("%Y-%m-%d")
                    time_str = f"{selected_hour}:{selected_minute}:00"
                    
                    # 중복 출석 방지
                    if is_already_checked_in(date_str, name):
                        st.warning(f"⚠️ {name}님은 이미 {date_str}에 출석 완료되었습니다.")
                    else:
                        # 지각 판별 로직
                        cutoff_h, cutoff_m = map(int, st.session_state.cutoff_time.split(":"))
                        cutoff_datetime = datetime.time(cutoff_h, cutoff_m)
                        
                        selected_time_obj = datetime.time(int(selected_hour), int(selected_minute))
                        if selected_time_obj <= cutoff_datetime:
                            status = "출석"
                        else:
                            status = "지각"
                            
                        # DB 저장
                        success = add_attendance_record(date_str, name, time_str, status, notes)
                        if success:
                            if status == "출석":
                                st.balloons()
                                st.success(f"🎉 {name}님, {time_str}에 정상 출석 처리되었습니다!")
                            else:
                                st.warning(f"⚠️ {name}님, {time_str}에 지각 처리되었습니다. (기준 시간: {st.session_state.cutoff_time})")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.subheader("💡 이용 안내")
        st.info(f"""
        - **기준 출석 시간**: `{st.session_state.cutoff_time}` 이전 출석 시 '정상 출석' 처리되며, 그 이후는 자동으로 '지각' 처리됩니다.
        - **중복 체크 방지**: 하루에 단 한 번만 출석 체크가 가능합니다.
        - **시간 임의 입력**: 부득이하게 제시간에 출석을 체크하지 못한 경우, 날짜와 시간을 수동으로 선택해 신청할 수 있습니다. (사유를 비고란에 기입해주세요.)
        """)
        
        # 오늘의 출석자 미니 전광판
        st.subheader("📢 오늘의 출석 현황")
        df_all = get_attendance_data()
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if not df_all.empty:
            df_today = df_all[df_all["날짜"] == today_str]
            if not df_today.empty:
                for idx, row in df_today.iterrows():
                    badge_style = "badge-present" if row["상태"] == "출석" else "badge-late"
                    st.markdown(f"""
                    <div style="padding:0.5rem; background:rgba(255,255,255,0.03); border-radius:8px; margin-bottom:0.5rem;">
                        <strong>{row['이름']}</strong> <span style="font-size:0.8rem; color:#A0A0B0;">({row['체크인 시간']})</span>
                        <span class="badge {badge_style}" style="float:right;">{row['상태']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("오늘 출석한 인원이 아직 없습니다.")
        else:
            st.caption("출석 데이터가 없습니다.")

# ----------------------------------------------------
# TAB 2: 통계 대시보드
# ----------------------------------------------------
with tab2:
    st.subheader("📊 출석 데이터 분석 대시보드")
    df = get_attendance_data()
    
    if df.empty:
        st.info("시각화할 출석 데이터가 존재하지 않습니다. 먼저 출석을 완료해주세요.")
    else:
        # 요약 카드 구성
        total_records = len(df)
        attendance_count = len(df[df["상태"] == "출석"])
        late_count = len(df[df["상태"] == "지각"])
        attendance_rate = (attendance_count / total_records * 100) if total_records > 0 else 0
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        with m_col1:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color:#A0A0B0; font-size:0.9rem;">총 누적 기록 수</span>
                <h2 style="margin: 0.5rem 0; font-weight:800; color:#E0E0E6;">{total_records}건</h2>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color:#2ecc71; font-size:0.9rem;">정상 출석 횟수</span>
                <h2 style="margin: 0.5rem 0; font-weight:800; color:#2ecc71;">{attendance_count}회</h2>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color:#f1c40f; font-size:0.9rem;">지각 횟수</span>
                <h2 style="margin: 0.5rem 0; font-weight:800; color:#f1c40f;">{late_count}회</h2>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color:#A88BEB; font-size:0.9rem;">정상 출석률</span>
                <h2 style="margin: 0.5rem 0; font-weight:800; color:#A88BEB;">{attendance_rate:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 차트 레이아웃
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 📈 일자별 출석/지각 분포")
            df_grouped = df.groupby(["날짜", "상태"]).size().reset_index(name="인원수")
            fig1 = px.bar(
                df_grouped,
                x="날짜",
                y="인원수",
                color="상태",
                barmode="stack",
                color_discrete_map={"출석": "#2ecc71", "지각": "#f1c40f"},
                template="plotly_dark"
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Inter",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with chart_col2:
            st.markdown("#### 🏆 최다 지각 및 성실 출석 인원 랭킹")
            # 개인별 통계 계산
            df_person = df.groupby("이름")["상태"].value_counts().unstack(fill_value=0).reset_index()
            if "출석" not in df_person.columns:
                df_person["출석"] = 0
            if "지각" not in df_person.columns:
                df_person["지각"] = 0
            
            df_person["총참여"] = df_person["출석"] + df_person["지각"]
            df_person["출석률"] = (df_person["출석"] / df_person["총참여"] * 100).round(1)
            
            fig2 = px.bar(
                df_person.sort_values(by="출석률", ascending=True),
                y="이름",
                x="출석률",
                orientation="h",
                text="출석률",
                labels={"출석률": "정상 출석률 (%)"},
                template="plotly_dark",
                color="출석률",
                color_continuous_scale="Purples"
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Inter",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        # 전체 상세 내역 테이블
        st.markdown("#### 📋 전체 기록 목록")
        st.dataframe(
            df.sort_values(by=["날짜", "체크인 시간"], ascending=[False, False]),
            use_container_width=True,
            column_config={
                "날짜": st.column_config.TextColumn("날짜"),
                "이름": st.column_config.TextColumn("이름"),
                "체크인 시간": st.column_config.TextColumn("체크인 시간"),
                "상태": st.column_config.TextColumn("상태"),
                "비고": st.column_config.TextColumn("비고")
            }
        )

# ----------------------------------------------------
# TAB 3: 관리 콘솔
# ----------------------------------------------------
with tab3:
    st.subheader("⚙️ 관리자 설정 및 데이터 관리")
    
    # 관리자 로그인 확인
    admin_input = st.text_input("🔑 관리자 암호 입력", type="password", help="기본 설정 암호는 'admin' 입니다.")
    
    if admin_input == st.session_state.admin_password:
        st.success("🔓 관리자 권한이 인증되었습니다.")
        
        set_col1, set_col2 = st.columns(2)
        
        with set_col1:
            st.markdown("### ⏰ 출석 설정 변경")
            new_cutoff = st.text_input("출석 인정 기준 시간 (HH:MM 포맷)", value=st.session_state.cutoff_time)
            new_pass = st.text_input("관리자 암호 변경", value=st.session_state.admin_password, type="password")
            
            if st.button("💾 설정 저장"):
                try:
                    # 유효한 시간 형식인지 체크
                    datetime.datetime.strptime(new_cutoff, "%H:%M")
                    save_settings(new_cutoff, new_pass)
                    st.success("설정이 안전하게 저장되었습니다!")
                    st.rerun()
                except ValueError:
                    st.error("시간 형식이 올바르지 않습니다. HH:MM 형식을 유지해주세요. (예: 09:00)")
                    
        with set_col2:
            st.markdown("### 📥 데이터 다운로드 & 관리")
            df_download = get_attendance_data()
            if not df_download.empty:
                csv = df_download.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV 파일로 백업 다운로드",
                    data=csv,
                    file_name=f"attendance_backup_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("다운로드할 데이터가 없습니다.")
                
            st.markdown("### 🗑️ 데이터 초기화 (주의)")
            if st.button("⚠️ 모든 출석 데이터 리셋"):
                if conn_configured:
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        empty_df = pd.DataFrame(columns=["날짜", "이름", "체크인 시간", "상태", "비고"])
                        conn.update(data=empty_df)
                        st.success("구글 스프레드시트의 출석 데이터가 초기화되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"구글 시트 초기화 실패: {e}")
                else:
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        st.success("로컬 데이터가 완전히 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.info("지울 데이터 파일이 존재하지 않습니다.")
    else:
        if admin_input != "":
            st.error("❌ 비밀번호가 올바르지 않습니다.")
        else:
            st.caption("비밀번호를 입력하여 관리자 메뉴를 활성화하세요.")
