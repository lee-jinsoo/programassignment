import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA Dashboard")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded_file:
            st.info("Please upload population_trends.csv.")
            return

        # Load & preprocess
        df = pd.read_csv(uploaded_file)
        df.replace('-', 0, inplace=True)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📄 Basic Stats", 
            "📈 Yearly Trend", 
            "📊 Regional Analysis", 
            "📋 Change Analysis", 
            "🗺️ Visualization"
        ])

        with tab1:
            st.subheader("Basic Statistics")
            st.write("Summary statistics:")
            st.write(df.describe())
            st.subheader("DataFrame Info")
            buffer = StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

        with tab2:
            st.subheader("Nationwide Population Forecast")
            national_df = df[df['지역'] == '전국'].copy().sort_values(by='연도')
            recent = national_df[national_df['연도'].isin(national_df['연도'].unique()[-3:])]
            avg_birth = recent['출생아수(명)'].mean()
            avg_death = recent['사망자수(명)'].mean()
            last_pop = national_df['인구'].iloc[-1]
            future = last_pop + (2035 - national_df['연도'].max()) * (avg_birth - avg_death)

            national_plot = national_df[['연도', '인구']]
            national_plot.loc[len(national_plot)] = [2035, future]

            fig, ax = plt.subplots()
            ax.plot(national_plot['연도'], national_plot['인구'], marker='o')
            ax.axvline(2035, linestyle='--', color='red')
            ax.text(2035, future, f"{int(future):,}", color='red')
            ax.set_title('Population Trend and Projection')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)

        with tab3:
            st.subheader("Regional 5-Year Change (Thousands & %)")
            df_region = df[df['지역'] != '전국'].copy()
            df_region['Region'] = df_region['지역'].map(region_map)
            recent5 = sorted(df_region['연도'].unique())[-5:]
            df_recent = df_region[df_region['연도'].isin(recent5)]
            pivot = df_recent.pivot(index='Region', columns='연도', values='인구')
            pop_diff = (pivot[recent5[-1]] - pivot[recent5[0]]) / 1000
            pop_rate = ((pivot[recent5[-1]] - pivot[recent5[0]]) / pivot[recent5[0]]) * 100

            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sorted_diff = pop_diff.sort_values(ascending=False)
            sns.barplot(x=sorted_diff.values, y=sorted_diff.index, ax=ax1, palette='viridis')
            ax1.set_title("5-Year Population Change (Thousands)")
            ax1.set_xlabel("Change (Thousands)")
            for i, v in enumerate(sorted_diff):
                ax1.text(v + 1, i, f"{v:.1f}", va='center')
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sorted_rate = pop_rate.loc[sorted_diff.index]
            sns.barplot(x=sorted_rate.values, y=sorted_rate.index, ax=ax2, palette='coolwarm')
            ax2.set_title("5-Year Population Growth Rate (%)")
            ax2.set_xlabel("Growth Rate (%)")
            for i, v in enumerate(sorted_rate):
                ax2.text(v + 0.2, i, f"{v:.1f}%", va='center')
            st.pyplot(fig2)

        with tab4:
            st.subheader("Top 100 Population Change Cases")
            df_diff = df[df['지역'] != '전국'].copy().sort_values(['지역', '연도'])
            df_diff['Change'] = df_diff.groupby('지역')['인구'].diff()
            top100 = df_diff[['연도', '지역', 'Change']].dropna().sort_values(by='Change', key=abs, ascending=False).head(100)
            top100['Region'] = top100['지역'].map(region_map)
            top100['Formatted Change'] = top100['Change'].apply(lambda x: f"{int(x):,}")

            def color_scale(val):
                val = float(val)
                if val > 0:
                    return f'background-color: rgba(0, 100, 255, {min(val / top100["Change"].max(), 1):.2f}); color: white;'
                elif val < 0:
                    return f'background-color: rgba(255, 80, 80, {min(-val / abs(top100["Change"].min()), 1):.2f}); color: white;'
                return ''

            styled_table = top100[['연도', 'Region', 'Formatted Change', 'Change']].copy()
            st.dataframe(
                styled_table.style.applymap(color_scale, subset=['Change'])
                                  .format({'Formatted Change': '{}'})
                                  .hide(axis="columns", subset=["Change"]),
                use_container_width=True
            )

        with tab5:
            st.subheader("Stacked Area Chart by Region")
            df_stack = df[df['지역'] != '전국'].copy()
            df_stack['Region'] = df_stack['지역'].map(region_map)
            pivot_stack = df_stack.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum')
            pivot_stack = pivot_stack.fillna(0).sort_index()

            fig3, ax3 = plt.subplots(figsize=(12, 6))
            pivot_stack.plot.area(ax=ax3, colormap='tab20')
            ax3.set_title("Population by Region Over Time")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            ax3.legend(loc='upper left', bbox_to_anchor=(1, 1), title='Region')
            st.pyplot(fig3)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()