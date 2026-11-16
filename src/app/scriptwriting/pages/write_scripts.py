import sys
import os

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    import streamlit as st
    from google import genai
    import pandas as pd
    import numpy as np
    from types import NoneType
    from google import genai
    from scriptwriting.tools.utils import *
    import pyperclip


except ImportError as e:
    import traceback
    print(f"Error importing required packages: {e}")
    print(traceback.format_exc())
    try:
        # If streamlit is successfully imported, show error in UI
        if 'st' in globals():
            st.error(
                f"Failed to import required packages. Please install them using: pip install -r requirements.txt\n\nError: {e}")
            st.stop()
    except:
        # If we can't even use streamlit, exit the program
        sys.exit(1)

# App configuration
# st.set_page_config(page_title="Write Scripts", page_icon="📝")


@st.cache_data
def load_data():
    features_df = pd.read_parquet('data/ScriptGen-data/script_gendata.parquet')

    def parse_list(x):
        if isinstance(x, np.ndarray):
            return list(x)
        if isinstance(x, NoneType):
            return []
    for col in features_df.columns:
        list_flag = features_df[col].apply(
            lambda x: isinstance(x, np.ndarray)).any()
        if list_flag:
            features_df[col] = features_df[col].apply(parse_list)
    return features_df


# st.title("Viết kịch bản video TikTok")
# st.write("[Empty for now]")

# Constants
API_KEY = "REDACTED_IN_ENV"  # vphacc096@gmail.com
DEFAULT_MODEL = "gemini-2.0-flash"
PAGE_TITLE = "Write Scripts"
PAGE_ICON = "📝"
COLUMN_GAP: str = "medium"

# Available AI Models
AVAILABLE_MODELS = [
    "gemini-2.5-pro-exp-03-25",
    "gemini-2.0-flash",         # Input: 1,048,576 tokens, Output: 8,192 tokens
    "gemini-2.0-pro-exp",       # Input: 2,048,576 tokens, Output: 8,192 tokens
    "gemini-2.0-flash-thinking-exp-1219",
    "gemini-2.0-flash-lite",    # Input: 1,048,576 tokens, Output: 8,192 tokens
    "gemini-1.5-flash",         # Input: 1,048,576 tokens, Output: 8,192 tokens
    "gemini-1.5-flash-8b",      # Input: 1,048,576 tokens, Output: 8,192 tokens
    "gemini-1.5-pro",           # Input: 2,097,152 tokens, Output: 8,192 tokens
    "learnlm-1.5-pro-experimental",
    "gemma-3-27b-it",
]


class ScriptGenerator:
    def __init__(self):
        self.init_page_config()
        self.init_session_state()
        self.model = self.get_model()
        # self.model = None
        self.features_df = self.load_data()
        self.client = genai.Client(api_key=API_KEY)

    def init_page_config(self):
        """Initialize Streamlit page configuration"""
        st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide",
                           initial_sidebar_state="expanded",)

    def init_session_state(self):
        """Initialize session state variables"""
        if 'formatted_script' not in st.session_state:
            st.session_state.formatted_script = None
        if 'updated_script_data' not in st.session_state:
            st.session_state.updated_script_data = None

    def get_model(self):
        """Get the selected AI model from sidebar"""
        return st.sidebar.selectbox(
            "Chọn mô hình AI:",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(DEFAULT_MODEL)
        )

    def load_data(self):
        """Load TikTok data with spinner"""
        with st.spinner("Đang tải dữ liệu TikTok..."):
            features_df = load_data()

        if features_df is None:
            st.error("Không thể tải dữ liệu TikTok. Vui lòng thử lại sau.")
            st.stop()

        return features_df

    def generate_script(self, user_description):
        """Generate script based on user description"""

        with st.spinner("Phân tích mô tả..."):
            # Generate labels from description
            label_dict = generate_labels_from_description(
                user_description, self.client, self.model)

            # Handle non-food content
            if label_dict is None:
                filtered_df = self.features_df
                filter_cat_df = self.features_df
            elif label_dict and label_dict['categories'] == 'Không liên quan ẩm thực':
                st.error(
                    "Yêu cầu của bạn không liên quan đến ẩm thực! Vui lòng thử lại với một mô tả khác.")
                return None
            else:
                # Extract duration if available
                duration = int(label_dict.pop("duration", None)) if label_dict.get(
                    "duration") is not None else None

                # Filter data based on labels
                filtered_df = filter_by_multiple_labels_unified(
                    self.features_df, label_dict, min_count=20)
                filter_cat_df = self.features_df[self.features_df['categories']
                                                 == label_dict['categories']]

            # Calculate statistics
            stats = self._calculate_statistics(filtered_df, filter_cat_df)

            # Use mean duration if not specified
            if duration is None:
                duration = stats['mean_duration']

            word_count = int(stats['mean_word_per_second'] * duration)
            max_output_tokens = int(word_count * 1.5)
            # max_output_tokens = 2000000

            # Adjusted for better performance
            print(f"Duration: {duration}")
            print(f"Max Word Count: {word_count}")
            print(f"Max Output Token: {max_output_tokens}")
            print(stats['mean_word_per_second'])

        st.success("🧠 Mô tả đã được giải mã!")

        # Generate and format script
        with st.spinner("Tạo kịch bản thô..."):
            plain_script = generate_plain_script(
                user_description, stats['transcript_sample_text'], word_count, self.client, self.model, max_output_tokens)
        st.success("🛠️ Bản nháp đầu tiên đã hoàn thành, chờ tinh chỉnh!")

        with st.spinner("Định dạng lại kịch bản..."):
            formatted_script = format_script_with_gemini(
                plain_script,
                stats['desc_sample_text'],
                stats['mean_desc_word_count'],
                stats['mean_word_per_second'],
                stats['mean_hashtag_count'],
                stats['top_10_hashtags_text'],
                self.client,
                self.model
            )
            print(f"Desc Word Count: {stats['mean_desc_word_count']}")

            # Save to session state
            st.session_state.formatted_script = formatted_script
            st.session_state.updated_script_data = formatted_script.copy()

        st.success("🎬 Kịch bản đã sẵn sàng!")
        return formatted_script

    def _calculate_statistics(self, filtered_df, filter_cat_df):
        """Calculate statistics from filtered dataframes"""
        stats = {
            'mean_word_count': int(filtered_df['transcript_word_count'].median()),
            'mean_duration': int(filtered_df['video.duration'].median()),
            'mean_word_per_second': filtered_df['word_per_second'].median(),
            'mean_hashtag_count': int(filtered_df['hashtag_count'].median()),
            'mean_desc_word_count': int(filtered_df['desc_word_count'].median()),
        }

        # Get top hashtags
        top_10_hashtags = filter_cat_df['hashtags'].explode(
        ).value_counts().head(10).index
        stats['top_10_hashtags_text'] = ', '.join(top_10_hashtags)

        # Get sample texts
        stats['transcript_sample_text'], stats['desc_sample_text'] = format_transcript_desc_examples(
            filtered_df, min_count=20)

        return stats

    def display_script_overview(self, script_data):
        """Display the script overview section"""
        st.markdown("### 📝 Tổng quan video")
        st.markdown(
            f"**🎬 Mô tả video:** {script_data.get('video_description', '')}")
        st.markdown(
            f"**⏱️ Độ dài dự kiến:** {script_data.get('duration', '')}")
        st.markdown(f"**📍 Bối cảnh:** {script_data.get('setting', '')}")
        st.markdown(f"**👤 Nhân vật:** {script_data.get('characters', '')}")
        st.markdown("---")

    def display_script_sections(self, script_data):
        """Display all script sections with edit functionality"""
        # Display overview
        self.display_script_overview(script_data)

        st.markdown("### 🎬 Kịch bản theo từng phần")

        # Process section deletions
        self._process_section_deletions()

        # Display each section
        for idx, section in enumerate(st.session_state.updated_script_data.get("main_content", [])):
            self._display_single_section(idx, section)

        return st.session_state.updated_script_data

    def _process_section_deletions(self):
        """Process any pending section deletions"""
        sections_to_delete = []
        for idx in range(len(st.session_state.updated_script_data.get("main_content", []))):
            if st.session_state.get(f"delete_section_{idx}", False):
                sections_to_delete.append(idx)
                st.session_state[f"delete_section_{idx}"] = False

        for idx in sorted(sections_to_delete, reverse=True):
            st.session_state.updated_script_data["main_content"].pop(idx)

    def _display_single_section(self, idx, section):
        """Display a single script section with edit functionality"""
        key_prefix = f"sec_{idx}"

        # Initialize edit mode state if not exists
        if f"{key_prefix}_edit" not in st.session_state:
            st.session_state[f"{key_prefix}_edit"] = False

        edit_mode = st.session_state[f"{key_prefix}_edit"]
        default_text = f"[{section['time_range']}] {section['title']}"

        # Title row with edit/save buttons
        self._display_section_header(
            key_prefix, section, default_text, edit_mode)

        # Content section (visual and dialogue)
        self._display_section_content(key_prefix, section, edit_mode)

    def _display_section_header(self, key_prefix, section, default_text, edit_mode):
        """Display the section header with edit/save buttons"""
        col_title, col_btns = st.columns([9, 1])

        with col_title:
            if edit_mode:
                time_title_input = st.text_input(
                    "⏱️ Thời gian & tiêu đề", default_text,
                    key=f"{key_prefix}_time_title",
                    label_visibility="collapsed"
                )
            else:
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; padding: 8px 16px; border-radius: 6px;">
                        <strong>{default_text}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_btns:
            if not edit_mode:
                if st.button("✏️", key=f"{key_prefix}_edit_btn", help="Sửa", use_container_width=True):
                    st.session_state[f"{key_prefix}_edit"] = True
                    st.rerun()
            else:
                if st.button("✅", key=f"{key_prefix}_save_btn", help="Lưu", use_container_width=True):
                    self._save_section_edits(key_prefix, section, default_text)
                    st.session_state[f"{key_prefix}_edit"] = False
                    st.rerun()

    def _save_section_edits(self, key_prefix, section, default_text):
        """Save edits made to a section"""
        time_title_raw = st.session_state.get(
            f"{key_prefix}_time_title", default_text)
        if "]" in time_title_raw:
            time_part, title_part = time_title_raw.split("]", 1)
            section["time_range"] = time_part.strip(" [")
            section["title"] = title_part.strip()

    def _display_section_content(self, key_prefix, section, edit_mode):
        """Display the content (visual and dialogue) of a section"""
        col1, col2 = st.columns([1, 2])

        if edit_mode:
            with col1:
                st.markdown("🎥 **Cảnh quay**")
                visual_input = st.text_area(
                    "🎥 Cảnh quay", section['visual_description'],
                    key=f"{key_prefix}_visual", height=100,
                    label_visibility="collapsed"
                )
            with col2:
                st.markdown("🗣️ **Lời thoại**")
                dialogue_input = st.text_area(
                    "🗣️ Lời thoại", section['dialogue'],
                    key=f"{key_prefix}_dialogue", height=100,
                    label_visibility="collapsed"
                )

            # Update section values
            if f"{key_prefix}_visual" in st.session_state:
                section["visual_description"] = visual_input
            if f"{key_prefix}_dialogue" in st.session_state:
                section["dialogue"] = dialogue_input
        else:
            with col1:
                st.markdown("🎥 **Cảnh quay**")
                st.markdown(section['visual_description'])
            with col2:
                st.markdown("🗣️ **Lời thoại**")
                st.markdown(f"\"{section['dialogue']}\"")

    def render_script_to_markdown(self, script_dict):
        md = []
        md.append("## 📝 Tổng quan video\n")
        if 'video_description' in script_dict:
            md.append(
                f"**📄 Mô tả video**: {script_dict['video_description']}\n")
        if 'duration' in script_dict:
            md.append(f"**⏱️ Độ dài dự kiến**: {script_dict['duration']}\n")
        if 'setting' in script_dict:
            md.append(f"**📍 Bối cảnh**: {script_dict['setting']}\n")
        if 'characters' in script_dict:
            md.append(f"**👤 Nhân vật**: {script_dict['characters']}\n")
        md.append("\n## 🎬 Kịch bản theo từng phần\n")
        for part in script_dict.get("main_content", []):
            time_range = part.get("time_range", "")
            title = part.get("title", "")
            visual = part.get("visual_description", "")
            dialogue = part.get("dialogue", "")

            md.append(f"#### **[{time_range}] {title}**")
            md.append(f"- **(Cảnh quay):** {visual}")
            md.append(f"- **(Lời thoại):** {dialogue.strip()}\"\n")
        return "\n\n".join(md)

    def display_download_section(self, json_script):
        markdown_script = self.render_script_to_markdown(
            json_script)

        left_col, right_col = st.columns(
            spec=2, gap=COLUMN_GAP, vertical_alignment="top",
            # border=True,
        )
        with left_col:
            if st.button(
                label="Sao chép kịch bản",
                key="copy_suggestion_button",
                help="Sao chép gợi ý vào clipboard",
                icon=":material/content_copy:",
                use_container_width=True,
            ):
                pyperclip.copy(markdown_script)
                st.success(
                    "Kịch bản đã được sao chép vào clipboard!", icon="✅")

        with right_col:
            st.download_button(
                label="Tải xuống kịch bản",
                key="download_suggestion_button",
                help="Tải xuống kịch bản dưới dạng file Markdown",
                data=markdown_script,
                file_name="script.md",
                mime="text/plain",
                on_click="ignore",
                icon=":material/download:",
                use_container_width=True,
            )

    def run(self):
        """Main application flow"""
        st.title("Tạo kịch bản TikTok")
        # with option_col_2:  # Column 2: Chọn mô hình AI
        # st.subheader(
        #     body=":gray-background[:blue[:material/smart_toy:]] Chọn mô hình AI",
        #     anchor="Chọn mô hình AI",
        # )

        # Select model
        # self.model = st.selectbox(
        #     label="**:blue[Bạn muốn tạo kịch bản như thế nào?:]**",
        #     options=AVAILABLE_MODELS,
        #     index=1
        # )

        # Expandable section for description input
        with st.expander("**:blue[📝 Nhập mô tả video]**", expanded=True):
            user_description = st.text_area(
                "Mô tả chi tiết về video TikTok bạn muốn tạo:",
                placeholder="Làm video TikTok hướng dẫn nấu mì tôm trứng siêu nhanh, siêu dễ cho sinh viên. Cần nhấn mạnh vào sự tiện lợi và hướng dẫn từng bước...",
                height=250  # Increased height for more space
            )

            # Add some example suggestions
            st.markdown("""
            **Một số chi tiết có thể gợi ý cho hệ thống:**
            - **Món ăn** và **mục tiêu video** (review, nấu, chia sẻ...)
            - **Cách triển khai** (kể chuyện, hướng dẫn, review...)
            - **Cách mở đầu, giọng điệu, tốc độ video**
            - Có **CTA** gì không (comment, chia sẻ, ghé quán...)
            - Ai là **người xem** chính (học sinh, dân văn phòng, nội trợ...)
            
            **Ví dụ**: Tôi muốn làm video quảng bá cho sản phẩm bánh tráng chấm phô mai của nhà tôi, cách nói chuyện gần gũi, có hướng dẫn cách ăn, giọng điệu từ tốn.
            """)

            # col1, col2, col3 = st.columns([2, 1, 2])
            # with col2:
            generate_button = st.button(
                "Tạo kịch bản", use_container_width=True, type='primary', icon=":material/auto_awesome:",
            )

            if generate_button and user_description:
                self.generate_script(user_description)

        # Display script if available
        if st.session_state.formatted_script:
            st.header("🎬 Kịch bản gợi ý")
            self.display_script_sections(st.session_state.formatted_script)
            self.display_download_section(st.session_state.formatted_script)


# Main execution
# if __name__ == "__main__":
app = ScriptGenerator()
app.run()
