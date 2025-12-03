import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Gemini Chatbot", layout="centered")

st.title("🟦 Gemini API 기반 챗봇")

st.write("""
이 앱은 **Google Gemini API**를 사용하여 동작합니다.

👉 사용 전 반드시 Streamlit Secrets에 다음을 추가해야 합니다:
```
GEMINI_API_KEY = "당신의 키"
```
""")

# API 설정
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# 세션 초기화
if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("💬 대화 내용")
for role, msg in st.session_state.history:
    if role == "user":
        st.markdown(f"**👤 사용자:** {msg}")
    else:
        st.markdown(f"**🤖 Gemini:** {msg}")

user_input = st.text_input("메시지를 입력하세요:")

# Gemini 답변 생성 함수
def get_gemini_reply(text):
    response = model.generate_content(text)
    return response.text

# 전송 버튼
if st.button("전송") and user_input:
    st.session_state.history.append(("user", user_input))
    try:
        bot_reply = get_gemini_reply(user_input)
    except Exception as e:
        bot_reply = f"오류 발생: {e}"
    st.session_state.history.append(("bot", bot_reply))
    st.experimental_rerun()

# 초기화
if st.button("대화 초기화"):
    st.session_state.history = []
    st.experimental_rerun()
