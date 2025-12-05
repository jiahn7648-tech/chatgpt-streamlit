import streamlit as st
import os
from google import genai
from google.genai import errors

# ==============================================================================
# 0. 일반 AI 비서 역할을 위한 시스템 지침 설정
# ==============================================================================
SYSTEM_INSTRUCTION = (
    "당신은 친절하고 유용한 일반 AI 어시스턴트입니다. "
    "모든 종류의 질문에 대해 명확하고 정확하며, 도움이 되는 정보를 제공해주세요. "
    "사용자가 어떤 주제로든 자유롭게 대화할 수 있도록 지원하며, 긍정적이고 친근한 태도를 유지해주세요."
)

# 1. API 키 설정 및 클라이언트 초기화
# Streamlit Cloud에 배포할 때는 'GEMINI_API_KEY'라는 이름의 환경 변수(Secrets)를 사용합니다.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # 로컬 환경에서 키가 없거나 Streamlit Cloud Secrets에 키가 없는 경우 오류 메시지 표시
    st.error("❌ 오류: 'GEMINI_API_KEY' 환경 변수 또는 Streamlit Secret이 설정되지 않았습니다.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
    st.stop()

# 사용할 모델 설정
MODEL_NAME = "gemini-2.5-flash"

# Streamlit UI 설정 (제목 변경)
st.set_page_config(page_title="Gemini 일반 챗봇", layout="centered")
st.title("💬 일반 대화형 챗봇: 제미나이")
st.caption("Gemini 모델로 구동되는, 무엇이든 물어볼 수 있는 평범한 AI 챗봇입니다.")
st.divider()

# 2. 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 Gemini 모델로 구동되는 일반 챗봇입니다. 무엇이든 물어보세요!"}
    ]

# 3. 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리 (텍스트 전용)
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 4-1. 사용자 메시지 기록 및 화면 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4-2. Gemini API 호출을 위한 대화 기록 준비
    history = []
    for message in st.session_state.messages:
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 4-3. 챗봇 응답 스트리밍
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=history,
                config={"system_instruction": SYSTEM_INSTRUCTION}
            )

            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") 
            
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
### 1. 라이브러리 설치
```bash
pip install streamlit google-genai
```

### 2. `requirements.txt` 파일 업데이트 (필수)
아래 내용을 `requirements.txt`에 꼭 넣어주세요.

```
streamlit
google-genai
```

### 3. API 키 설정 (중요!)
Streamlit Cloud의 'Secrets' 설정에 **`GEMINI_API_KEY`**와 여러분의 API 키를 입력해주세요.

### 4. 앱 실행
```bash
streamlit run app.py
```
"""
)
