
import os
import sys
import streamlit as st
from google import genai
from typing import List, Dict
import pyperclip
import time


# ================================================================
# *_____________________ [Define constants] _____________________*
# ================================================================
GEMINI_MODELS_FILE: str = "models/gemini_models.txt"
PROMPT_TEMPLATE_FOLDER: str = "data/prompts/research"
RESEARCH_SYSTEM_PROMPT_PATH: str = os.path.join(
    PROMPT_TEMPLATE_FOLDER, "system_prompt_template.md")
DEFAULT_USER_PROMPT_PATH: str = os.path.join(
    PROMPT_TEMPLATE_FOLDER, "user_prompt_template.md")


# ================================================================
# *_________________ [Define helper functions] __________________*
# ================================================================
@st.cache_data
def read_prompt_file(file_path: str) -> str:
    """ Read and cache prompt content from a markdown file. """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        return content
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


@st.cache_data
def read_available_gemini_models(file_path: str) -> List[str]:
    """ Read and cache available Gemini models from a text file. """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            models: List[str] = [line.strip() for line in file.readlines()]
        return models
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return []


def standardize_response(response: str) -> str:
    """ Standardize the response from Gemini API by removing unnecessary parts """

    # Remove leading and trailing whitespace
    response = response.strip()
    # Remove first line
    if response.startswith("```"):
        response = response.split("\n", 1)[1]
    # Remove last line
    if response.endswith("```"):
        response = response.rsplit("\n", 1)[0]
    # Remove leading and trailing whitespace
    response = response.strip()

    return response


# ================================================================
# *____________ [Setup Streamlit page configuration] ____________*
# ================================================================
# App configuration
st.set_page_config(
    # Research on topics
    page_title="Nghiên cứu chủ đề",  # "Research on topics"
    page_icon="🔍",
    layout="wide",
)
# Tiêu đề trang và mô tả
st.title(":blue[🔍 Nghiên cứu về một chủ đề]")
st.markdown(
    "Tạo ra các giải thích chi tiết về nhiều chủ đề khác nhau với sự hỗ trợ của AI")


# ================================================================
# *___________________ [Read prompt template] ___________________*
# ================================================================
# System prompt
system_prompt: str = read_prompt_file(file_path=RESEARCH_SYSTEM_PROMPT_PATH)
# Default user prompt
default_user_prompt: str = read_prompt_file(file_path=DEFAULT_USER_PROMPT_PATH)


# ================================================================
# *__________________ [UI for selecting model] __________________*
# ================================================================
# Read available AI models
available_models: List[str] = read_available_gemini_models(
    file_path=GEMINI_MODELS_FILE)

# Get selected model
with st.sidebar:
    model = st.selectbox(
        label="**Chọn mô hình AI:**",
        options=available_models,
        index=available_models.index("gemini-2.0-flash"),  # Default model
    )
    # Hiển thị thông tin mô hình được chọn
    st.info(f"Bạn đã chọn mô hình: **{model}**")


# ================================================================
# *________________ [UI for editing user prompt] ________________*
# ================================================================
# Set start session time
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
# Prompt customization section
if 'research_prompt' not in st.session_state:
    st.session_state.research_prompt = default_user_prompt
# If user has updated the prompt
if 'has_updated_prompt' not in st.session_state:
    st.session_state.has_updated_prompt = False
# If user has reset the prompt to default
if 'has_reset_prompt' not in st.session_state:
    st.session_state.has_reset_prompt = False


# with st.expander("View/Edit Research Prompt", expanded=False):
with st.expander(f"**:blue[Xem/Chỉnh sửa prompt]**", expanded=False):
    st.markdown(
        "Đây là hướng dẫn gửi đến mô hình AI. Bạn có thể sửa đổi nó để phù hợp hơn với nhu cầu của bạn.")

    # Text area for editing the prompt
    custom_prompt = st.text_area(
        "**Bạn có thể tùy chỉnh prompt bên dưới:**",
        value=st.session_state.research_prompt,
        height=300,
        key="research_prompt_editor"
    )

    col1, col2 = st.columns(spec=2, gap="large", vertical_alignment="top")

    with col1:
        if st.button(
            label="**:material/published_with_changes: Cập nhật prompt**",
            help="Cập nhật prompt tùy chỉnh của bạn",
            use_container_width=True,
        ):
            st.session_state.research_prompt = custom_prompt
            st.session_state.has_updated_prompt = True
            st.session_state.start_time = time.time()
            st.rerun()
        if st.session_state.has_updated_prompt:
            st.success("✅ Đã cập nhật prompt!")
            st.session_state.has_updated_prompt = False

    with col2:
        if st.button(
            label="**:material/refresh: Khôi phục prompt mặc định**",
            help="Khôi phục lại prompt mặc định",
            use_container_width=True,
        ):
            st.session_state.research_prompt = default_user_prompt
            st.session_state.has_reset_prompt = True
            st.session_state.start_time = time.time()
            st.rerun()
        if st.session_state.has_reset_prompt:
            st.session_state.has_reset_prompt = False
            st.success("✅ Đã khôi phục prompt mặc định!")


# ================================================================
# *______________ [UI for entering video topic] ___________________*
# ================================================================
# Tạo khu vực cho người dùng nhập chủ đề cần nghiên cứu
st.header(
    body=":orange-background[:orange[:material/screen_search_desktop:]] Nhập chủ đề mà bạn muốn nghiên cứu",
)
# Main content
topic = st.text_area(
    "**:orange[Hãy chọn một chủ đề mà bạn cảm thấy thú vị để tiến hành nghiên cứu]**",
    height=100,
    placeholder="Chẳng hạn: Đánh giá món ăn, Nấu ăn, Du lịch, v.v.",
)
# Thể hiện 1 ví dụ minh họa
with st.expander(label="**Ví dụ minh họa**", expanded=True):
    st.write("Đánh giá món ăn")


# ================================================================
# *_______________ [Logic for researching topic] ________________*
# ================================================================
# Store last research response in session state
if 'last_research_response' not in st.session_state:
    st.session_state.last_research_response = ""

# Button to generate content
research_button: bool = st.button(
    label="**Tiến hành nghiên cứu**",
    key="research_button",
    help="Nhấn để tiến hành nghiên cứu chủ đề mà bạn đã nhập.",
    type="primary",
    icon=":material/explore:",
    use_container_width=True,
)

# Generate content when button is pressed
if research_button:
    if not topic.strip():
        # Không cho nghiên cứu nếu không có chủ đề nào được nhập
        st.warning("**⚡️ Vui lòng nhập chủ đề để tiến hành nghiên cứu!**")
    else:
        # Research on the topic
        with st.spinner(text="⏳ Đang nghiên cứu...", show_time=True):
            # Call the Gemini API to generate content
            client = genai.Client(
                api_key="REDACTED_IN_ENV")
            response = client.models.generate_content(
                model=model,
                contents=[
                    system_prompt,
                    f"Hãy giúp tôi tạo ra một bài giải thích chi tiết về chủ đề {topic}." +
                    st.session_state.research_prompt,
                ]
            )
            # Standardize the response
            response = standardize_response(response.text)
            # Store the last research response in session state
            st.session_state.last_research_response = response
            # Reset 2 flags for updating and resetting the prompt
            st.session_state.has_updated_prompt = False
            st.session_state.has_reset_prompt = False


# Hiển thị kết quả nghiên cứu nếu có
if st.session_state.last_research_response != "":
    st.divider()

    # Display results
    st.header(
        body=":orange-background[:orange[:material/emoji_objects:]] Kết quả nghiên cứu",
    )
    # Display the response in markdown format
    st.markdown(st.session_state.last_research_response)

    # Hiển thị các nút chức năng
    left_col, right_col = st.columns(
        spec=2, gap="medium", vertical_alignment="top",
    )
    # Tạo nút sao chép nội dung nghiên cứu vào clipboard
    with left_col:
        # Tạo nút sao chép nội dung vào clipboard
        if st.button(
            label="Sao chép nội dung",
            key="research_copy_button",
            help="Sao chép nội dung nghiên cứu vào clipboard",
            icon=":material/content_copy:",
            use_container_width=True,
        ):
            # Copy the research response to clipboard
            pyperclip.copy(st.session_state.last_research_response)
            st.success("Nội dung đã được sao chép vào clipboard!", icon="✅")
    # Tạo nút tải xuống nội dung nghiên cứu dưới dạng file markdown
    with right_col:
        # Cho phép người download nội dung
        st.download_button(
            label="Tải xuống nội dung",
            help="Tải xuống nội dung dưới dạng file Markdown",
            data=f"# Chủ đề: {topic}\n\n{st.session_state.last_research_response}",
            file_name="research_topic.md",
            mime="text/plain",
            on_click="ignore",
            icon=":material/download:",
            use_container_width=True,
        )
