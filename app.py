import streamlit as st
import os
import io # 파일 처리를 위해 다시 추가
import base64 # Base64 인코딩을 위해 다시 추가
from google import genai
from google.genai import errors

# ==============================================================================
# 0. 일반 AI 비서 역할을 위한 시스템 지침 설정 (파일 분석 기능 포함)
# ==============================================================================
SYSTEM_INSTRUCTION = (
    "당신은 친절하고 유용한 일반 AI 어시스턴트입니다. "
    "사용자가 업로드한 파일을 첨부하면, 그 파일의 내용(이미지, 텍스트 등)을 이해하고 질문에 답변하는 데 활용해야 합니다. "
    "파일은 새로운 파일이 업로드되거나 명시적으로 제거되기 전까지 세션에 첨부된 상태로 유지됩니다. "
    "일반 지식, 분석, 아이디어 등 모든 종류의 질문에 대해 명확하고 정확하며, 도움이 되는 정보를 제공해주세요. "
    "긍정적이고 친근한 태도를 유지하며 답변하세요."
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
st.set_page_config(page_title="Gemini 멀티모달 챗봇", layout="centered")
st.title("💬 파일 첨부 가능 일반 챗봇: 제미나이")
st.caption("파일(이미지, 문서 등)을 첨부하고 무엇이든 물어볼 수 있는 AI 챗봇입니다.")
st.divider()

# 2. 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 파일을 분석하며 대화할 수 있는 챗봇입니다. 파일을 올리고 질문하시거나, 바로 대화를 시작해주세요!"}
    ]
# 파일 정보를 세션에 유지하며 첨부할 상태 추가
if "attached_file" not in st.session_state:
    st.session_state.attached_file = None

# 3. 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 및 파일 업로드 처리 (멀티모달 기능 재추가)

# 파일 업로더 재추가 (st.session_state.file_uploader를 통해 값에 접근)
uploaded_file = st.file_uploader("여기에 파일(이미지, CSV 등)을 업로드하세요. (선택 사항)", type=None, key="file_uploader")
prompt = st.chat_input("업로드한 파일이나 일반적인 내용에 대해 질문하세요...")


# 4-1. 파일이 업로드되면 세션 상태에 저장합니다. (새 파일은 이전 파일을 덮어씁니다.)
# 이 로직은 st.experimental_rerun() 없이, 세션 상태를 저장하고 UI만 즉시 초기화하도록 변경되었습니다.
if uploaded_file is not None:
    # 4-1-1. 파일 내용을 Base64로 인코딩하고 세션에 첨부된 파일로 저장
    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type
    
    # 2MB 이상의 파일은 경고 메시지 표시 (Streamlit/API 제약 사항 고려)
    if len(file_bytes) > 2 * 1024 * 1024:
        st.warning("⚠️ 파일 크기가 너무 큽니다. 2MB 이하의 파일만 안정적으로 처리될 수 있습니다.")

    base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
    
    # 파일 정보를 세션에 저장
    st.session_state.attached_file = {
        "data": base64_encoded_data,
        "mimeType": mime_type,
        "name": uploaded_file.name
    }
    
    # UI 피드백을 표시하기 위해 채팅창에 메시지를 추가합니다.
    if st.session_state.messages[-1].get("role") != "assistant" or "파일 첨부 완료!" not in st.session_state.messages[-1].get("content", ""):
        st.session_state.messages.append({"role": "assistant", "content": f"✅ **파일 첨부 완료!** `{uploaded_file.name}`. 이 파일은 새로운 파일을 업로드하기 전까지 모든 질문에 계속 첨부됩니다. 질문을 입력해주세요."})
    
    # 파일이 업로드되면, 업로더 위젯의 값만 None으로 설정하여 다음 업로드를 준비합니다.
    # st.session_state.file_uploader = None 대신, 
    # Streamlit은 파일이 처리된 후 이 부분을 자동으로 None으로 처리하거나,
    # prompt 입력 후 자동 rerun을 통해 처리되도록 이 부분을 제거하고 다음 로직에 의존합니다.
    # st.experimental_rerun() 제거

# 4-2. 사용자 입력(프롬프트)이 있을 경우에만 API 호출 실행
if prompt:
    # API 요청에 포함될 내용물(parts) 리스트 초기화
    contents_parts = []
    
    # 4-2-1. 첨부된 파일이 있으면 현재 요청에 추가합니다. (초기화 로직 없음)
    if st.session_state.attached_file is not None:
        attached_file = st.session_state.attached_file
        
        # 파일 파트 추가 (텍스트 앞에 오도록)
        contents_parts.append({
            "inlineData": {
                "data": attached_file["data"],
                "mimeType": attached_file["mimeType"]
            }
        })
        # 참고: attached_file 상태는 유지되어 다음 질문에도 계속 포함됩니다.
    
    # 4-2-2. 텍스트 프롬프트 처리
    # 사용자 메시지 기록 및 UI 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 텍스트 파트 추가 
    contents_parts.append({"text": prompt})


    # 4-3. Gemini API 호출을 위한 대화 기록 준비
    history_to_send = []
    # Gemini API는 'user'와 'model' 역할을 사용하며, 마지막 메시지를 제외한 모든 메시지를 history에 추가
    role_map = {"user": "user", "assistant": "model"}

    for message in st.session_state.messages[:-1]: 
        if message["role"] in role_map:
            # 파일이 첨부된 경우, 해당 메시지는 텍스트만 보냅니다.
            history_to_send.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 최종 contents 구성: 이전 대화 기록 + 현재 요청 (텍스트 + 파일)
    final_contents = history_to_send + [{ "role": "user", "parts": contents_parts }]


    # 4-4. 챗봇 응답 스트리밍
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

    # 4-5. 최종 응답을 채팅 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 및 배포 방법 안내 (사이드바)
st.sidebar.header("실행 및 배포 방법")
st.sidebar.markdown(
    """
### 1. 라이브러리 설치 (파일 분석 관련 라이브러리 추가)
멀티모달 기능을 활용하기 위해 데이터 분석 라이브러리를 추가하는 것이 좋습니다.

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
