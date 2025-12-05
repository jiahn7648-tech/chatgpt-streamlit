import streamlit as st

import os
from google import genai

# 1. API 키 설정 및 클라이언트 초기화
# 환경 변수에서 API 키를 가져옵니다.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Gemini 클라이언트 초기화 실패: {e}")
    st.stop()

# 사용할 모델 설정
MODEL_NAME = "gemini-2.5-flash"

# Streamlit UI 설정
st.set_page_config(page_title="Gemini Streamlit 챗봇", layout="centered")
st.title("✨ Gemini 기반 스트리밍 챗봇")
st.caption("Google Generative AI API와 Streamlit으로 만든 간단한 챗봇입니다.")

# 2. 채팅 기록 초기화
# Streamlit의 session_state를 사용하여 채팅 기록을 유지합니다.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 Gemini 기반 챗봇입니다. 무엇을 도와드릴까요?"}
    ]

# 3. 채팅 기록 표시
# 이전 대화 내용을 UI에 보여줍니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 사용자 메시지를 채팅 기록에 추가 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini 모델에 전달할 메시지 형식으로 변환
    # role: 'user' 또는 'model'
    history = []
    for message in st.session_state.messages:
        # 어시스턴트의 역할은 'assistant' 대신 'model'로 매핑해야 합니다.
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # Gemini API 호출 및 스트리밍 응답 처리
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # client.models.generate_content_stream을 사용하여 스트리밍 방식으로 응답을 받습니다.
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=history
            )

            # 스트리밍된 응답을 청크별로 화면에 표시합니다.
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") # 타이핑 효과를 위한 커서
            
            # 최종 응답 표시 및 커서 제거
            message_placeholder.markdown(full_response)
            
        except genai.errors.APIError as e:
            error_message = f"API 호출 중 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message
        except Exception as e:
            error_message = f"예상치 못한 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message

    # 최종 응답을 채팅 기록에 저장합니다.
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 방법 안내
st.sidebar.header("실행 방법")
st.sidebar.markdown(
    """
1. **API 키 설정:**
   `GEMINI_API_KEY` 환경 변수에 Google AI Studio에서 발급받은 API 키를 설정해야 합니다.

   ```bash
   export GEMINI_API_KEY="YOUR_API_KEY"
   ```

2. **필요한 라이브러리 설치:**
   ```bash
   pip install streamlit google-genai
   ```

3. **Streamlit 앱 실행:**
   ```bash
   streamlit run app.py
   ```

4. **웹 브라우저에서 접속:**
   자동으로 열리는 웹 브라우저나 콘솔에 표시된 주소로 접속하여 챗봇을 사용합니다.
"""
)
