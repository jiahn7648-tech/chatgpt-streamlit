import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="Gemini Chatbot", layout="centered")

# Title
st.title("🟦 Gemini API 기반 챗봇")
st.write("""
이 앱은 **Google Gemini API**로 동작합니다.

👉 먼저 Streamlit Secrets에 아래 항목을 추가하세요:GEMINI_API_KEY = "당신의_Gemini_API_Key"

# --- Gemini API 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 무료 계정에서 가장 안정적인 모델
MODEL_NAME = "gemini-pro"
model = genai.GenerativeModel(MODEL_NAME)

# 세션 초기화
if "history" not in st.session_state:
    st.session_state.history = []

# 대화 표시
st.subheader("💬 대화 내용")
for role, msg in st.session_state.history:
    if role == "user":
        st.markdown(f"**👤 사용자:** {msg}")
    else:
        st.markdown(f"**🤖 Gemini:** {msg}")

# 입력창
user_input = st.text_input("메시지를 입력하세요:")

# Gemini 응답 함수
def get_gemini_reply(text):
    response = model.generate_content(text)
    return response.text

# 전송 버튼
if st.button("전송") and user_input:
    st.session_state.history.append(("user", user_input))

    try:
        reply = get_gemini_reply(user_input)
    except Exception as e:
        reply = f"오류 발생: {e}"

    st.session_state.history.append(("bot", reply))
    st.rerun()

# 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.history = []
    st.rerun()
