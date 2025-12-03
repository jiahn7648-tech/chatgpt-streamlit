import streamlit as st

st.set_page_config(page_title="Simple Chat App", layout="centered")

st.title("🟦 ChatGPT 스타일 로컬 채팅앱 (API 없이)")

# 설명
st.write("""
이 버전은 **OpenAI API 없이도** 동작하는 **가짜(로컬 시뮬레이션) 챗봇**입니다.

👉 실제 ChatGPT처럼 동작하진 않지만, **웹 인터페이스 + 채팅 UI + 대화기록**은 그대로 구현됩니다.

나중에 API 키가 생기면 아주 쉽게 실제 모델로 교체할 수 있도록 코드 구조도 깔끔하게 만들어져 있습니다.
""")

# 세션 초기화
if "history" not in st.session_state:
    st.session_state.history = []

# 채팅 출력
st.subheader("💬 대화 내용")
for role, msg in st.session_state.history:
    if role == "user":
        st.markdown(f"**👤 사용자:** {msg}")
    else:
        st.markdown(f"**🤖 봇:** {msg}")

# 입력창
user_input = st.text_input("메시지를 입력하세요:")

# 응답 생성(로컬 시뮬레이션)
def fake_ai_response(text):
    return f"'{text}' 라고 하셨군요! 아직 API 키가 없어서 제가 직접 대답하는 척 하는 중입니다 🙂"

# 전송 버튼
if st.button("전송") and user_input:
    st.session_state.history.append(("user", user_input))
    bot_reply = fake_ai_response(user_input)
    st.session_state.history.append(("bot", bot_reply))
    st.experimental_rerun()

# 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.history = []
    st.experimental_rerun()
