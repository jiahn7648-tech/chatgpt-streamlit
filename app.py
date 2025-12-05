import streamlit as st
import os
from google import genai
from google.genai import errors

# 1. API 키 설정 및 클라이언트 초기화
# Streamlit Cloud에 배포할 때는 'GEMINI_API_KEY'라는 이름의 환경 변수(Secrets)를 사용합니다.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # 로컬 환경에서 키가 없거나 Streamlit Cloud Secrets에 키가 없는 경우 오류 메시지 표시
    st.error("❌ 오류: 'GEMINI_API_KEY' 환경 변수 또는 Streamlit Secret이 설정되지 않았습니다.")
    st.error("👉 사이드바의 '실행 방법' 섹션을 참고하여 API 키를 설정해주세요.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
    st.stop()

# 사용할 모델 설정 (빠르고 가성비 좋은 모델)
MODEL_NAME = "gemini-2.5-flash"

# Streamlit UI 설정
st.set_page_config(page_title="Gemini Streamlit 챗봇", layout="centered")
st.title("✨ Gemini 기반 스트리밍 챗봇")
st.caption("Google Generative AI API와 Streamlit으로 만든 실시간 응답 챗봇입니다.")
st.divider()

# 2. 채팅 기록 초기화
# st.session_state를 사용하여 사용자와 봇의 대화 내용을 저장합니다.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 Gemini 모델로 구동되는 챗봇입니다. 무엇이든 물어보세요!"}
    ]

# 3. 채팅 기록 표시
# session_state에 저장된 모든 대화 내용을 화면에 보여줍니다.
for message in st.session_state.messages:
    # 챗봇 메시지는 'assistant', 사용자 메시지는 'user' 아이콘을 사용합니다.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 4-1. 사용자 메시지 기록 및 화면 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4-2. Gemini API 호출을 위한 대화 기록 준비
    # Gemini API는 'user'와 'model' 역할을 사용합니다.
    history = []
    for message in st.session_state.messages:
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 4-3. 챗봇 응답 스트리밍
    with st.chat_message("assistant"):
        # 응답이 실시간으로 표시될 공간을 만듭니다.
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # generate_content_stream을 사용하여 응답을 청크별로 받습니다.
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=history
            )

            # 스트림에서 청크를 받아 누적하고 화면에 실시간으로 업데이트합니다.
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    # 응답이 작성되는 것처럼 보이도록 커서(▌)를 추가합니다.
                    message_placeholder.markdown(full_response + "▌") 
            
            # 최종 응답 표시 및 커서 제거
            message_placeholder.markdown(full_response)
            
        except errors.APIError as e:
            error_message = f"API 호출 중 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message
        except Exception as e:
            error_message = f"예상치 못한 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message

    # 4-4. 최종 응답을 채팅 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 및 배포 방법 안내 (사이드바)
st.sidebar.header("실행 및 배포 방법")
st.sidebar.markdown(
    """
이 챗봇을 실행하려면 세 가지 단계가 필요합니다.

### 1. 라이브러리 설치
터미널에서 이 명령어를 실행하세요:
```bash
pip install streamlit google-genai
```

### 2. API 키 설정 (중요!)
Google AI Studio에서 발급받은 키를 설정해야 합니다.

**로컬 실행 시:**
```bash
export GEMINI_API_KEY="당신의_API_키"
```
**Streamlit Cloud 배포 시:**
Streamlit Cloud 대시보드의 'Secrets' 설정에 `GEMINI_API_KEY`와 키 값을 추가해야 합니다.

### 3. 앱 실행
```bash
streamlit run app.py
```
"""
)
