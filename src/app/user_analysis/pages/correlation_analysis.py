import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from google import genai
from typing import Dict, Any, List
from plotly import figure_factory
# from user_analysis.utils.footer import display_footer


# ================================================================
# *_____________________ [Define constants] _____________________*
# ================================================================
# Hằng số
COLORS_RGBA: List[str] = [
    "rgba(99, 110, 250, 0.9)",  # Xanh dương
    "rgba(239, 85, 59, 0.8)",   # Đỏ
    "rgba(0, 204, 150, 0.7)"    # Xanh lá
]
METRICS: List[str] = [
    "stats.followerCount", "stats.heartCount", "stats.videoCount"]
METRIC_LABELS: List[str] = [
    "Số người theo dõi", "Số lượt thích", "Số lượng video"]
DARK_GRAY: str = "#444444"
# CLEANED_USER_DATA_FILE: str = "data/interim/cleaned_user_info.csv"
CLEANED_USER_DATA_FILE: str = "data/processed/cleaned_user_info.parquet"


# ================================================================
# *____________________ [Utility functions] _____________________*
# ================================================================
def apply_styles():
    """ Thay đổi CSS cho web page """
    st.markdown("""
        <style>
        .main-title {
            font-size: 28px;
            font-weight: bold;
            color: #FFFFFF;
            text-align: center;
            padding-bottom: 20px;
        }
        .subheader {
            font-size: 20px;
            font-weight: bold;
            color: #E0E0E0;
            padding-top: 10px;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        }
        .stExpander {
            border-radius: 10px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """ Tính toán ma trận tương quan """
    return df.corr()


# @st.cache_data
def select_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """ Chọn các cột từ DataFrame """
    return df[columns]


# Hàm giúp tạo nhận xét và rút ra insights từ kết quả phân tích và trực quan hóa dữ liệu
@st.cache_data(show_spinner=False)
def generate_insights(prompt: str, api_key: str) -> str:
    """ Tạo nhận xét từ Gemini API """
    # Generate content
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        print(f"Lỗi khi tạo nội dung: {e}")
        return ""


# Tạo 1 module dành riêng cho việc rút trích insights từ biểu đồ
# và thể hiện lên trang web
def display_AI_generated_insights(prompt: str, api_key: str) -> None:
    """ End-to-end module để rút trích insights từ biểu đồ và hiện thị lên trang web """

    with st.expander(
            label=":blue-background[:blue[**:material/auto_awesome: Nhận xét từ AI**]]",
            expanded=True):
        # Tạo nhận xét từ Gemini API
        with st.spinner(text="Đang tạo nhận xét từ AI...", show_time=True):
            insights = generate_insights(prompt=prompt, api_key=api_key)
            if not insights:
                st.error("Hiện tại hệ thống đang quá tải, vui lòng thử lại sau.")
            else:
                st.markdown(insights)


# Tải dữ liệu
@st.cache_data
def load_user_data() -> pd.DataFrame:
    """ Tải và lưu trữ dữ liệu người dùng đã được làm sạch từ tệp """
    if CLEANED_USER_DATA_FILE.endswith(".csv"):
        return pd.read_csv(CLEANED_USER_DATA_FILE)
    elif CLEANED_USER_DATA_FILE.endswith(".parquet"):
        # Đọc tệp Parquet
        return pd.read_parquet(CLEANED_USER_DATA_FILE)

    return None


@st.cache_data
def create_scatter_matrix(df: pd.DataFrame, template: str) -> go.Figure:
    """ Tạo một biểu đồ ma trận phân tán chỉ hiển thị tam giác dưới bên trái """

    df = select_columns(df, METRICS)
    density = px.histogram(df, x=[0, 1, 2], histnorm='probability density')
    df_corr = get_correlation_matrix(df)

    fig = figure_factory.create_scatterplotmatrix(
        df=df, diag='histogram',
        height=600,
    )

    # 1.How can I specify a single color for all the plots?
    for i in range(9):
        fig.data[i]['marker']['color'] = "rgba(99, 110, 250, 0.9)"
        fig.data[i]['marker']['opacity'] = 0.8
        fig.data[i]['marker']['line']['width'] = 0.5
        fig.data[i]['marker']['line']['color'] = "rgba(0, 0, 0, 0.5)"

    # 4.Is there a way to include the correlation coefficient (say, computed from df.corr())
    # in the upper right corner of the non-diagonal plots?
    for r, x, y in zip(df_corr.values.flatten(),
                       ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9'],
                       ['y1', 'y2', 'y3', 'y4', 'y5', 'y6', 'y7', 'y8', 'y9']):
        if r == 1.0:
            pass
        else:
            # Map to column names
            if x in ['x1', 'x2', 'x3']:
                col_y = METRICS[0]
                col_x = METRICS[int(x[-1]) - 1]
            elif x in ['x4', 'x5', 'x6']:
                col_y = METRICS[1]
                col_x = METRICS[int(x[-1]) - 4]
            elif x in ['x7', 'x8', 'x9']:
                col_y = METRICS[2]
                col_x = METRICS[int(x[-1]) - 7]

            # # Add a correlation coefficient annotation to the scatter plot
            # fig.add_annotation(x=df[col_x].max() * 0.90,
            #                    y=df[col_y].max() * 0.90,
            #                    xref=x, yref=y,
            #                    showarrow=False,
            #                    # Add a border to the annotation box: gray
            #                    bordercolor='rgba(128, 128, 128, 0.8)',
            #                    borderwidth=1,
            #                    text='R:'+str(round(r, 2)),
            #                    font=dict(size=12, color='black'),
            #                    # Background color for the annotation box: light yellow
            #                    bgcolor='rgba(255, 255, 0, 0.2)',
            #                    )

            # Create a line for each scatter plot
            fig.add_shape(type="line",
                          x0=df[col_x].min(), y0=df[col_y].min(),
                          x1=df[col_x].max(), y1=df[col_y].max(),
                          line=dict(color="rgba(255, 0, 0, 0.5)", width=2),
                          xref=x, yref=y,
                          )

    # Change the name of each x-axis and y-axis
    # * Theo trục x
    for col_number in range(1, 4):
        fig.update_xaxes(title_text=METRIC_LABELS[col_number-1],
                         row=3, col=col_number)
    # * Theo trục y
    for row_number in range(1, 4):
        fig.update_yaxes(title_text=METRIC_LABELS[row_number-1],
                         row=row_number, col=1)

    # Update title and layout
    fig.update_layout(
        # Đặt tiêu đề cho biểu đồ
        title=dict(
            text="🔍 Ma trận phân tán",
            font=dict(size=22, color=DARK_GRAY),
            x=0,     # Adjust horizontal position
            # y=0.95,  # Adjust vertical position
        ),
        template=template,
        margin=dict(b=0, t=80, l=0, r=0),  # Giảm khoảng cách giữa các cạnh
    )

    return fig


@st.cache_data
def create_correlation_heatmap(df: pd.DataFrame, template: str):
    """ Tạo một biểu đồ nhiệt tương quan chỉ hiển thị tam giác dưới bên trái """

    # Tính toán ma trận tương quan
    correlation_matrix = df[METRICS].corr()

    # Tạo mặt nạ cho tam giác trên
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    masked_correlation = correlation_matrix.mask(mask)

    global masked_correlation_latex
    masked_correlation_latex = masked_correlation.to_latex()

    # Vẽ biểu đồ nhiệt
    fig = px.imshow(
        masked_correlation,
        aspect="equal",
        color_continuous_scale="Blues",
        # labels=dict(x="Chỉ số", y="Chỉ số", color="Tương quan"),
        # Kích thước biểu đồ
        height=600,
        text_auto=".2f",
    )
    # Increase the font size of the text in the heatmap
    fig.update_traces(textfont_size=16)
    # Update layout
    fig.update_layout(
        xaxis=dict(tickvals=[0, 1, 2], ticktext=METRIC_LABELS),
        yaxis=dict(tickvals=[0, 1, 2], ticktext=METRIC_LABELS),
        template=template,
        title=dict(
            text="📊 Biểu đồ nhiệt tương quan",
            font=dict(size=22, color=DARK_GRAY),
            x=0,  # Adjust horizontal position
            # y=0.95,  # Adjust vertical position
        ),
        # Show color bar in horizontal orientation
        coloraxis_colorbar=dict(
            orientation="h",
            title="Hệ số tương quan",
            thicknessmode="pixels",
            thickness=20,
            lenmode="pixels",
            len=300,
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=0.90,
            title_side="top",
            title_font=dict(size=14, color=DARK_GRAY),
            # Increase the font size of the color bar labels
            tickfont=dict(size=12),
        ),
        # Hide grid lines
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        margin=dict(b=0, t=80, l=0, r=0),  # Giảm khoảng cách giữa các cạnh
    )

    # Update size of x and y axis labels
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))

    # Rotate y-axis labels
    fig.update_yaxes(tickangle=-90)

    return fig


@st.cache_data
def create_histogram(df: pd.DataFrame, metric: str, bins: int,
                     log_scale: bool, color: str, template: str,
                     metric_title: str):
    """ Tạo một biểu đồ histogram dựa trên chỉ số đã chọn """
    # titles = {
    #     'stats.followerCount': "Phân phối người theo dõi",
    #     'stats.heartCount': "Phân phối lượt thích",
    #     'stats.videoCount': "Phân phối số lượng video"
    # }
    fig = px.histogram(
        df,
        x=metric,
        nbins=bins,
        log_y=log_scale,
        color_discrete_sequence=[color],
        height=450,
        marginal="box",
        # title=titles[metric]
    )
    fig.update_layout(
        template=template, bargap=0.1, showlegend=False,
        # Show title
        title=dict(
            text=f"📊 Biểu đồ phân phối {metric_title}",
            font=dict(size=22, color=DARK_GRAY),
            x=0,  # Adjust horizontal position
            # y=0.95,  # Adjust vertical position
        ),
        margin=dict(b=0, t=80, l=0, r=0),  # Giảm khoảng cách giữa các cạnh
    )
    # Chỉnh sửa trục x
    # (chỉ riêng cho histogram, không phải cho boxplot)
    fig.update_xaxes(title_text=metric_title, title_font=dict(size=16),
                     row=1, col=1)

    return fig


# ================================================================
# *_______________________ [Basic setup] ________________________*
# ================================================================
# Cấu hình Streamlit
st.set_page_config(
    page_title="User Correlation Analysis",
    page_icon="📊",
    layout="wide",
)
# Tiêu đề và mô tả
st.title("📊 Phân tích tương quan giữa các chỉ số thống kê của TikToker")
st.markdown(
    "Khám phá mối quan hệ giữa số lượng người theo dõi, số lượt thích và số lượng video của các TikToker với các hình ảnh trực quan có khả năng tương tác.",
    # help="Sử dụng thanh bên để tùy chỉnh phân tích của bạn"
)


# ================================================================
# *_______________ [Read data and set up styles] ________________*
# ================================================================
# Áp dụng kiểu dáng và tải dữ liệu
apply_styles()
df = load_user_data()

# Xác định màu sắc cho biểu đồ
theme = "Sáng"
plotly_template = "plotly_white" if theme == "Tối" else "plotly_dark"


# ================================================================
# *_________________ [Overview and statistics] __________________*
# ================================================================
st.divider()
# Thống kê tóm tắt
with st.container():
    st.header("Tổng quan về dữ liệu")
    col1, col2, col3, col4 = st.columns(spec=4, gap="small")
    with col1:
        st.metric(label=":material/functions: Tổng số TikToker",
                  value=f"{len(df):,}",
                  help="Tổng số TikToker trong tập dữ liệu",
                  border=True,
                  )
    with col2:
        st.metric(label=":material/people: Số người theo dõi trung bình",
                  value=f"{df['stats.followerCount'].mean():,.0f}",
                  help="Số người theo dõi trung bình của TikToker",
                  border=True,
                  )
    with col3:
        st.metric(label=":material/favorite_border: Số lượt thích trung bình",
                  value=f"{df['stats.heartCount'].mean():,.0f}",
                  help="Số lượt thích trung bình của TikToker",
                  border=True,
                  )
    with col4:
        st.metric(label=":material/ondemand_video: Số lượng video trung bình",
                  value=f"{df['stats.videoCount'].mean():,.0f}",
                  help="Số lượng video trung bình của TikToker",
                  border=True,
                  )


# ================================================================
# *___________________ [Correlation analysis] ___________________*
# ================================================================
st.header("Phân tích tương quan giữa các chỉ số")

# Chia 2 cột cho biểu đồ phân tán và biểu đồ nhiệt
scatter_plot_col, heatmap_col = st.columns(
    spec=[0.6, 0.4], gap="small",
    vertical_alignment="top", border=True
)
with scatter_plot_col:  # Scatter plot with histogram
    # st.markdown("#### 🔍 Ma trận phân tán")
    scatter_fig = create_scatter_matrix(df, plotly_template)
    st.plotly_chart(scatter_fig, use_container_width=True)
with heatmap_col:  # Heatmap
    # st.markdown("#### 📊 Biểu đồ nhiệt tương quan")
    heatmap_fig = create_correlation_heatmap(df, plotly_template)
    st.plotly_chart(heatmap_fig, use_container_width=True)

# Dùng AI để rút ra insights từ biểu đồ
correlation_analysis_prompt = f"""
Hãy phân tích mối tương quan giữa 'Số người theo dõi', 'Số lượt thích' và 'Số lượng video' của các TikToker dựa trên dữ liệu được cung cấp. Viết một đoạn phân tích súc tích (khoảng 250-350 từ) tập trung vào:

1. Mức độ tương quan (mạnh, trung bình, yếu) giữa các cặp biến
2. Hướng tương quan (dương/âm) và ý nghĩa thực tế của nó
3. Các điểm bất thường hoặc xu hướng đáng chú ý từ biểu đồ phân tán
4. Các hàm ý cho người sáng tạo nội dung TikTok

Dữ liệu phân tích:

1. Biểu đồ phân tán thể hiện mối quan hệ giữa ba chỉ số. Biểu đồ này sẽ được đính kèm dưới dạng byte:
{scatter_fig.to_image()}

2. Bảng ma trận tương quan giữa các chỉ số (hệ số Pearson). Dưới đây là bảng thống kê thể hiện các thông tin này dưới dạng LaTeX:
{get_correlation_matrix(select_columns(df, METRICS)).to_latex()}

3. Thông tin bổ sung: 
    - Hệ số tương quan từ 0.7-1.0: tương quan mạnh
    - Hệ số tương quan từ 0.3-0.7: tương quan trung bình
    - Hệ số tương quan từ 0.0-0.3: tương quan yếu

Cấu trúc phân tích nên bao gồm:
- Tổng quan về mức độ tương quan chung giữa các biến
- Phân tích chi tiết từng cặp tương quan quan trọng 
- Kết luận và gợi ý thực tiễn cho người sáng tạo nội dung

Hãy bắt đầu phân tích trực tiếp mà không cần dùng các cụm từ giới thiệu như "Dựa trên dữ liệu..." hoặc "Theo biểu đồ...".
"""
display_AI_generated_insights(
     prompt=correlation_analysis_prompt,
     api_key="REDACTED_IN_ENV")


# ================================================================
# *__________________ [Distribution analysis] ___________________*
# ================================================================
st.header("Phân tích phân phối của các chỉ số")

# Tạo 2 cột, cột bên trái cho người dùng lựa chọn cài đặt và cột bên phải cho biểu đồ
setting_col, histogram_col = st.columns(
    spec=[0.2, 0.8], gap="medium",
    vertical_alignment="top", border=False
)
with setting_col:  # Cột bên trái cho người dùng lựa chọn cài đặt
    with st.expander(
        label="Chọn các chỉ số để trực quan hóa",
        expanded=True,
    ):
        # Cho phép người dùng chọn các chỉ số để trực quan hóa
        st.markdown("#### ⚙️ Tùy chọn trực quan hóa")
        chart_option = st.selectbox(
            label="**:blue[Chọn chỉ số để trực quan hóa]**",
            options=METRIC_LABELS,
            help="Chọn một chỉ số để trực quan hóa phân phối của nó"
        )
        num_bins = st.slider(
            label="**:blue[Số lượng bins]**",
            min_value=10, max_value=100, value=50, step=5,
            help="Điều chỉnh độ chi tiết của histogram"
        )
        log_scale = st.checkbox(
            label="**:blue[Sử dụng thang đo logarit]**",
            value=True,
            help="Bật để trực quan hóa dữ liệu lệch tốt hơn"
        )
with histogram_col:  # Cột bên phải cho biểu đồ
    # st.markdown("#### 📊 Biểu đồ phân phối")

    # Ánh xạ chỉ số đã chọn với tên cột trong DataFrame
    # và chỉ số màu sắc tương ứng
    metric_map = {
        "Số người theo dõi": ('stats.followerCount', 0),
        "Số lượt thích": ('stats.heartCount', 1),
        "Số lượng video": ('stats.videoCount', 2),
    }
    metric, color_idx = metric_map[chart_option]

    # Histogram động
    with st.spinner(f"Đang tạo biểu đồ phân phối cho `{chart_option}`...", show_time=True):
        hist_fig = create_histogram(
            df=df, metric=metric, bins=num_bins, log_scale=log_scale,
            color=COLORS_RGBA[color_idx], template=plotly_template,
            metric_title=chart_option
        )
        st.plotly_chart(hist_fig, use_container_width=True)

# Dùng AI để rút ra insights từ biểu đồ
distribution_analysis_prompt = f"""
Hãy giúp tôi viết 1 đoạn nhận xét về phân phối '{chart_option}' của các TikToker. Đoạn nhận xét này nên ngắn gọn, xúc tích, tập trung vào những điểm nổi bật từ phân phối quan sát được. Đoạn văn chỉ nên có khoảng 250 đến 350 từ.

Tôi sẽ cung cấp cho bạn 2 thông tin về dữ liệu mà tôi đã phân tích.
Đầu tiên là một biểu đồ có sự kết hợp giữa histogram ở bên dưới và boxplot ở bên trên thể hiện phân phối của '{chart_option}'. Biểu đồ này cho thấy phân phối của '{chart_option}' của các TikToker trong bộ dữ liệu. Biểu đồ này sẽ được đính kèm dưới dạng byte:
{hist_fig.to_image()}

Thứ hai là một bảng thể hiện một số giá trị thống kê cơ bản cho '{chart_option}'. Bảng này bao gồm các thông tin như giá trị trung bình, độ lệch chuẩn, các giá trị tứ phân vị và các giá trị cực trị. Dưới đây là bảng thống kê thể hiện các thông tin này dưới dạng LaTeX:
{df[metric].describe().to_latex()}

Hãy trả về câu trả lời bắt đầu với cụm từ: "Phân phối ...". Đừng bắt đầu câu trả lời bằng các cụm từ như: "Dựa trên ...".
"""
with histogram_col:  # Cột bên phải cho biểu đồ
    display_AI_generated_insights(
        prompt=distribution_analysis_prompt,
        api_key="REDACTED_IN_ENV")


# ================================================================
# *______________________ [Download data] _______________________*
# ================================================================
st.divider()
st.header("Tải dữ liệu")

st.markdown(
    "Tải xuống dữ liệu đã được sử dụng trong biểu đồ phân tích tương quan và phân phối.",
    help="Tải xuống dữ liệu đã được sử dụng trong biểu đồ phân tích tương quan và phân phối."
)
# Tạo một nút tải xuống cho dữ liệu đã chọn
data_to_download = select_columns(df, METRICS)
st.download_button(
    label="**📥 Nhấn vào đây để tải dữ liệu**",
    data=data_to_download.to_csv(index=False),
    file_name="tiktok_creator_metrics.csv",
    mime="text/plain",
    help="Tải dữ liệu được sử dụng trong biểu đồ này dưới dạng tệp CSV",
    on_click="ignore",
    type="primary",
    # use_container_width=True,
)
