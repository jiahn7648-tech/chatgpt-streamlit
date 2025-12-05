import streamlit as st
import os
import io # 파일 처리를 위해 추가
import base64 # Base64 인코딩을 위해 추가
from google import genai
from google.genai import errors

# ==============================================================================
# 0. 데이터/이미지 분석 비서 역할을 위한 시스템 지침 설정 (멀티모달 재도입)
# ==============================================================================
SYSTEM_INSTRUCTION = (
    "당신은 구글 코랩(Colab) 환경에 최적화된 이미지 및 데이터 분석 전문 비서입니다. "
    "주요 업무는 사용자의 업로드 파일(이미지, CSV 등)을 분석하고, 텍스트 질문에 답변하며, "
    "관련 파이썬 코드(데이터 처리, 시각화 등)를 제공하는 것입니다. "
    "사용자가 업로드한 파일을 기반으로 질문하면, 파일의 내용, 이미지의 시각적 요소 등을 이해하고 자세히 분석하여 대화에 활용해야 합니다. "
    "코드 설명은 주석과 함께 제공하며, 모든 코드는 구글 코랩 환경에서 바로 실행 가능하도록 작성해야 합니다. "
    "친절하고 전문적인 태도를 유지하며 답변하세요."
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
st.set_page_config(page_title="이미지 분석 챗봇", layout="centered")
st.title("🖼️ 파일 분석 & 대화형 비서: 제미나이")
st.caption("업로드된 이미지나 데이터를 분석하며 대화하는 전문 AI 비서입니다.")
st.divider()

# 2. 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 이미지나 데이터를 분석해 드리는 전문가입니다. 파일을 올리고 질문하시거나, 바로 대화를 시작해주세요!"}
    ]

# 3. 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 및 파일 업로드 처리 (멀티모달 재도입)

# 파일 업로더 추가
uploaded_file = st.file_uploader("여기에 파일(이미지, CSV 등)을 업로드하세요.", type=None, key="file_uploader")
prompt = st.chat_input("업로드한 파일이나 데이터에 대해 질문하세요...")


# 4-1. 사용자 입력(프롬프트 또는 파일)이 있을 경우에만 실행
if prompt or uploaded_file:
    # API 요청에 포함될 내용물(parts) 리스트 초기화
    contents_parts = []
    
    # 4-2. 파일 업로드 처리 (멀티모달 부분)
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        
        # 파일 내용을 Base64로 인코딩
        base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')

        # 파일 파트 추가
        contents_parts.append({
            "inlineData": {
                "data": base64_encoded_data,
                "mimeType": mime_type
            }
        })
        
        # 파일이 업로드되었음을 대화 기록에 표시
        file_message = f"**파일 업로드 완료:** `{uploaded_file.name}` ({mime_type} 형식)"
        st.session_state.messages.append({"role": "user", "content": file_message})
        # UI에 파일 업로드 메시지 표시
        with st.chat_message("user"):
            st.markdown(file_message)
            
    # 4-3. 텍스트 프롬프트 처리
    if prompt:
        # 텍스트 파트 추가
        contents_parts.append({"text": prompt})
        # 사용자 메시지 기록 및 UI 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

    # 4-4. Gemini API 호출을 위한 대화 기록 준비
    history_to_send = []
    # 마지막 메시지(현재 요청)를 제외한 이전 대화 기록만 포함
    for message in st.session_state.messages[:-1]: 
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history_to_send.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 최종 contents 구성: 이전 대화 기록 + 현재 요청 (텍스트 + 파일)
    final_contents = history_to_send + [{ "role": "user", "parts": contents_parts }]


    # 4-5. 챗봇 응답 스트리밍
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=final_contents, # <--- 멀티모달 Contents 사용
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

    # 4-6. 최종 응답을 채팅 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 및 배포 방법 안내 (사이드바)
st.sidebar.header("실행 및 배포 방법")
st.sidebar.markdown(
    """
### 1. 라이브러리 설치 (업데이트 필요!)
파일 처리 및 분석을 위해 추가 라이브러리가 필요합니다.

```bash
pip install streamlit google-genai pandas matplotlib seaborn
```

### 2. `requirements.txt` 파일 업데이트 (필수)
아래 내용을 `requirements.txt`에 꼭 넣어주세요.

```
streamlit
google-genai
pandas
matplotlib
seaborn
```

### 3. API 키 설정 (중요!)
Streamlit Cloud의 'Secrets' 설정에 **`GEMINI_API_KEY`**와 여러분의 API 키를 입력해주세요.

### 4. 앱 실행
```bash
streamlit run app.py
```
"""
)
