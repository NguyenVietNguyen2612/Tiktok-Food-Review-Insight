import streamlit as st
import os
from google import genai
from typing import List, Dict
import pyperclip


# ================================================================
# *_____________________ [Define constants] _____________________*
# ================================================================
GEMINI_MODELS_FILE: str = "models/gemini_models.txt"
PROMPT_TEMPLATE_FOLDER: str = "data/prompts/suggestion"
COLUMN_GAP: str = "medium"

OPTION_FOOD_REVIEW: str = "Video review món ăn hoặc quán ăn"
OPTION_MUKBANG: str = "Video mukbang"
OPTION_COOKING: str = "Video hướng dẫn nấu ăn"
VIDEO_TYPES: List[str] = [
    OPTION_FOOD_REVIEW,
    OPTION_MUKBANG,
    OPTION_COOKING
]
VIDEO_TYPE_TO_PROMPT: Dict[str, str] = {
    OPTION_FOOD_REVIEW: os.path.join(PROMPT_TEMPLATE_FOLDER, "food_review_template.md"),
    OPTION_MUKBANG: os.path.join(PROMPT_TEMPLATE_FOLDER, "mukbang_template.md"),
    OPTION_COOKING: os.path.join(PROMPT_TEMPLATE_FOLDER, "cooking_template.md"),
}


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


def generate_suggestion(system_prompt: str, model: str,
                        user_description: str) -> str:
    """ Generate video suggestions using Google's Gemini API. """

    # Generate content
    try:
        client = genai.Client(
            api_key="REDACTED_IN_ENV")
        response = client.models.generate_content(
            model=model,
            contents=[
                system_prompt,
                user_description,
            ],
        )
        return response.text
    except Exception as e:
        st.error(f"Lỗi khi tạo nội dung: {e}")
        return ""


# ================================================================
# *____________ [Setup Streamlit page configuration] ____________*
# ================================================================
# Cấu hình page
st.set_page_config(
    page_title="Gợi ý quay video ẩm thực",
    page_icon="🍜",
    layout="wide",
)
# Đặt tiêu đề của page
st.title("Hệ thống gợi ý quay video chủ đề ẩm thực")


# ================================================================
# *_________ [UI for selecting model and type of video] _________*
# ================================================================
# Tạo 2 columns cho người dùng lựa chọn
option_col_1, option_col_2 = st.columns(
    spec=2, gap=COLUMN_GAP, vertical_alignment="top",
    border=True,
)
with option_col_1:  # Column 1: Chọn loại video
    st.subheader(
        body=":gray-background[:blue[:material/video_library:]] Chọn loại video",
        anchor="Chọn loại video",
    )
    # Chọn loại video mà người dùng muốn thực hiện
    video_type = st.radio(
        label="**:blue[Hãy chọn loại video mà bạn muốn thực hiện:]**",
        options=VIDEO_TYPES,
        index=0,
    )
with option_col_2:  # Column 2: Chọn mô hình AI
    st.subheader(
        body=":gray-background[:blue[:material/smart_toy:]] Chọn mô hình AI",
        anchor="Chọn mô hình AI",
    )
    # Read available models from a file
    available_gemini_models = read_available_gemini_models(
        file_path=GEMINI_MODELS_FILE)
    # Select model
    model = st.selectbox(
        label="**:blue[Chọn mô hình AI mà bạn muốn sử dụng:]**",
        options=available_gemini_models,
        index=0
    )

# Tạo 2 columns để thể hiện thông tin về loại video và mô hình đã chọn
info_col_1, info_col_2 = st.columns(
    spec=2, gap=COLUMN_GAP, vertical_alignment="top",
    # border=True,
)
with info_col_1:  # Info về loại video đã chọn
    st.info(f"Bạn đã chọn loại video: **{video_type}**")
with info_col_2:  # Info về mô hình đã chọn
    st.info(f"Bạn đã chọn mô hình: **{model}**")


# ================================================================
# *____________ [UI for entering video description] _____________*
# ================================================================
# Tạo khu vực cho người dùng nhập mô tả video
st.header(
    body=":orange-background[:orange[:material/description:]] Mô tả video của bạn",
    anchor="Mô tả video của bạn",
)
user_description = st.text_area(
    label="**:orange[Hãy nhập mô tả chi tiết về video ẩm thực mà bạn muốn thực hiện:]**",
    value="",
    key="user_description",
    placeholder="Nhập mô tả video tại đây...",
    height=140,
)
# Thể hiện 1 ví dụ minh họa
with st.expander(label="**Ví dụ minh họa**", expanded=True):
    st.write("Tôi muốn tìm hiểu cách quay video review một quán bán đồ ăn vặt cho học sinh sinh viên trên con đường Cách mạng Tháng Tám. Theo như tôi tìm hiểu thì quán này có rất nhiều món ăn vặt phù hợp với giới trẻ như: bánh tráng trộn, bánh tráng nướng, bánh tráng cuốn, phở ly full topping hải sản, mỳ ly với nước súp lẩu thái, v.v.. Hãy đề xuất cho tôi những lời khuyên hữu ích về cách quay video, cách trò chuyện với chủ quán, cách giới thiệu món ăn, cách tạo không khí vui vẻ và hấp dẫn cho video. Tôi muốn video này có thể thu hút được sự chú ý của các bạn trẻ và tạo cảm giác muốn đến quán ăn thử ngay lập tức. Hãy cung cấp cho tôi một số mẹo và chiến lược để thực hiện điều này. Tôi cũng muốn biết về các xu hướng hiện tại trong việc quay video review món ăn vặt và những điều cần tránh khi thực hiện video này.")


# ================================================================
# *_____________ [Logic for generating suggestions] _____________*
# ================================================================
# Khởi tạo session state cho gợi ý nếu chưa có
if "suggestion" not in st.session_state:
    st.session_state.suggestion = ""

# Generate suggestions
generate_button: bool = st.button(
    label="**Tạo gợi ý**",
    key="generate_button",
    help="Nhấn để nhận gợi ý cho video của bạn",
    type="primary",
    icon=":material/auto_awesome:",
    use_container_width=True,
)
if generate_button:
    if not user_description.strip():
        st.warning(
            ":warning: Vui lòng nhập mô tả về video của bạn trước khi tạo gợi ý."
        )
    else:
        with st.spinner(
            text="⏳ Đang tạo gợi ý...", show_time=True,
        ):
            # Ánh xạ từ loại video sang tệp prompt
            prompt_file: str = VIDEO_TYPE_TO_PROMPT[video_type]
            # Đọc nội dung prompt từ tệp
            system_prompt: str = read_prompt_file(prompt_file)
            # Tạo gợi ý cho video thông qua API
            st.session_state.suggestion = generate_suggestion(
                system_prompt=system_prompt,
                model=model,
                user_description=user_description,
            )

# Hiển thị gợi ý nếu có
if st.session_state.suggestion:
    st.divider()
    # Hiển thị tiêu đề cho phần gợi ý
    st.header(
        body=":orange-background[:orange[:material/tips_and_updates:]] Gợi ý cho video của bạn",
        anchor="Gợi ý cho video của bạn",
    )
    # Hiển thị gợi ý
    st.markdown(st.session_state.suggestion)

    # Hiển thị các nút chức năng
    left_col, right_col = st.columns(
        spec=2, gap=COLUMN_GAP, vertical_alignment="top",
        # border=True,
    )
    # Tạo nút sao chép gợi ý vào clipboard
    with left_col:
        # Tạo nút sao chép gợi ý
        if st.button(
            label="Sao chép gợi ý",
            key="copy_suggestion_button",
            help="Sao chép gợi ý vào clipboard",
            icon=":material/content_copy:",
            use_container_width=True,
        ):
            # Copy the suggestion to clipboard
            pyperclip.copy(st.session_state.suggestion)
            st.success("Gợi ý đã được sao chép vào clipboard!", icon="✅")
    # Tạo nút tải xuống gợi ý dưới dạng tệp văn bản
    with right_col:
        st.download_button(
            label="Tải xuống gợi ý",
            key="download_suggestion_button",
            help="Tải xuống gợi ý dưới dạng file Markdown",
            data=st.session_state.suggestion,
            file_name="video_suggestion.md",
            mime="text/plain",
            on_click="ignore",
            icon=":material/download:",
            use_container_width=True,
        )
