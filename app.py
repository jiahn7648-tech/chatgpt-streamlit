"""
Streamlit ChatGPT-like app
- 파일명: streamlit_chatgpt_app.py
- 사용: GitHub에 푸시한 뒤 Streamlit Cloud(share.streamlit.io)에서 배포

요구사항 (requirements.txt에 추가):
streamlit
openai

배포 전 설정:
- Streamlit Cloud의 Secrets 또는 GitHub Actions/환경 변수에 OPENAI_API_KEY를 추가하세요.
  (Streamlit Cloud: Settings -> Secrets -> 키 이름: OPENAI_API_KEY, 값: 당신의 API 키)

간단 기능:
- 왼쪽 사이드바에서 시스템 프롬프트와 모델을 선택
- 메시지 히스토리 보존 (세션 스테이트)
- OpenAI Chat Completions API 호출
- 에러 처리 및 토큰 사용량 표시

주의: 이 코드는 예제용이며, 실제 서비스로 배포하기 전에 요금, 보안(입력 검증/비속어 필터링/속도 제한) 등을 점검하세요.
"""

import os
import streamlit as st
from typing import List, Dict

try:
    import openai
except Exception as e:
    st.error("openai 패키지가 설치되어 있지 않습니다. requirements.txt에 'openai'를 추가하고 설치하세요.")
    raise

st.set_page_config(page_title="ChatGPT-lite (Streamlit)", layout="wide")

# ------------------------- 설정 및 유틸리티 -------------------------

def get_api_key() -> str:
    # 먼저 st.secrets에서 찾고, 없으면 환경 변수에서 찾음
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.environ.get("OPENAI_API_KEY", "")

API_KEY = get_api_key()
if not API_KEY:
    st.sidebar.warning("OPENAI_API_KEY가 설정되어 있지 않습니다. 배포 시 Streamlit Secrets 또는 환경 변수에 추가하세요.")
else:
    openai.api_key = API_KEY


# ------------------------- 세션 초기화 -------------------------
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

if "generated" not in st.session_state:
    st.session_state.generated = []

if "user_inputs" not in st.session_state:
    st.session_state.user_inputs = []

if "usage" not in st.session_state:
    st.session_state.usage = {}


# ------------------------- 사이드바 컨트롤 -------------------------
st.sidebar.title("설정")
model = st.sidebar.selectbox("모델 선택", options=["gpt-3.5-turbo", "gpt-4o", "gpt-4"])
system_prompt = st.sidebar.text_area("시스템 프롬프트 (초기 지시)", value=st.session_state.history[0]["content"], height=120)
if st.sidebar.button("시스템 프롬프트 적용"):
    st.session_state.history[0]["content"] = system_prompt

clear = st.sidebar.button("채팅 초기화")
if clear:
    st.session_state.history = [{"role": "system", "content": "You are a helpful assistant."}]
    st.session_state.generated = []
    st.session_state.user_inputs = []
    st.session_state.usage = {}

# ------------------------- 레이아웃 -------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.header("ChatGPT-like (Streamlit)")

    # 채팅 메시지 출력
    chat_placeholder = st.container()

    with chat_placeholder:
        for i, user_msg in enumerate(st.session_state.user_inputs):
            st.markdown(f"**사용자:** {user_msg}")
            st.markdown(f"**어시스턴트:** {st.session_state.generated[i]}")

    # 입력 폼
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input("메시지를 입력하세요...", key="user_input")
        submitted = st.form_submit_button("전송")

    if submitted and user_input:
        # 히스토리에 사용자 메시지 추가
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.user_inputs.append(user_input)

        # OpenAI 호출
        if not API_KEY:
            st.error("OPENAI API 키가 설정되어 있지 않아 요청을 보낼 수 없습니다.")
        else:
            try:
                with st.spinner("응답 생성 중..."):
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=st.session_state.history,
                        max_tokens=1024,
                        temperature=0.2,
                    )

                assistant_text = response["choices"][0]["message"]["content"].strip()
                st.session_state.generated.append(assistant_text)
                st.session_state.history.append({"role": "assistant", "content": assistant_text})

                # 사용량 기록
                if "usage" in response:
                    st.session_state.usage = response["usage"]

                # 재렌더링을 위해 페이지를 새로 고침하지 않고도 메시지가 보이게 함
                st.experimental_rerun()

            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")

with col2:
    st.subheader("대화 요약 & 정보")
    if st.session_state.usage:
        st.write("**토큰 사용량**")
        st.write(st.session_state.usage)

    st.write("**현재 히스토리 길이**: {} 메시지".format(len(st.session_state.history)))
    st.write("**사용자 메시지 수**: {}".format(len(st.session_state.user_inputs)))

    st.markdown("---")
    st.write("배포 팁:")
    st.write("1. GitHub에 이 파일과 requirements.txt를 올리고 Streamlit Cloud에 연결하세요.")
    st.write("2. Streamlit Secrets에 OPENAI_API_KEY를 추가하세요.")
    st.write("3. 필요하면 모델과 토큰 제한을 조정하세요.")


# ------------------------- 끝 -------------------------

# 로컬 테스트용
if __name__ == '__main__':
    st.write("이 스크립트는 Streamlit 앱으로 실행되어야 합니다. 터미널에서 'streamlit run streamlit_chatgpt_app.py'를 실행하세요.")
