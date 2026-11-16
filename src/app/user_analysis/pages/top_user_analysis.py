import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from google import genai
from typing import Tuple, List, Dict
# from user_analysis.utils.footer import display_footer


# ================================================================
# *_____________________ [Define constants] _____________________*
# ================================================================
DARK_GRAY: str = "#444444"
# CLEANED_USER_DATA_FILE: str = "data/interim/cleaned_user_info.csv"
CLEANED_USER_DATA_FILE: str = "data/processed/cleaned_user_info.parquet"
CHART_OPTIONS: Dict[str, Tuple[str, str, str]] = {
    "Số lượt thích": ("stats.heartCount", "reds", "Tổng số lượt thích (tim)"),
    "Số lượng video": ("stats.videoCount", "greens", "Tổng số video"),
    "Số người theo dõi": ("stats.followerCount", "blues", "Tổng số người theo dõi"),
    "Tỷ lệ tương tác": ("engagement_rate", "purples", "Tỷ lệ tương tác")
}


# ================================================================
# *____________________ [Utility functions] _____________________*
# ================================================================
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
@st.cache_data(persist="disk")
def load_user_data() -> pd.DataFrame:
    """ Tải và lưu trữ dữ liệu người dùng đã được làm sạch từ tệp """
    if CLEANED_USER_DATA_FILE.endswith(".csv"):
        return pd.read_csv(CLEANED_USER_DATA_FILE)
    elif CLEANED_USER_DATA_FILE.endswith(".parquet"):
        # Đọc tệp Parquet
        return pd.read_parquet(CLEANED_USER_DATA_FILE)

    return None


# Hàm tính tỷ lệ tương tác
@st.cache_data
def calculate_engagement_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """ Tính toán tỷ lệ tương tác cho từng người dùng """
    df['engagement_rate'] = df['stats.heartCount'] / \
        df['stats.videoCount'].replace(0, 1)
    return df


# Lọc top N người dùng theo một chỉ số nhất định
@st.cache_data(persist="disk")
def filter_top_n_users(df: pd.DataFrame, metric: str, n: int, sort_order: str) -> pd.DataFrame:
    """ Lọc top N người dùng theo một chỉ số nhất định """

    # Lọc dữ liệu theo chỉ số đã chọn
    top_data = (df.nlargest(n, metric) if sort_order == "Giảm dần"
                else df.nsmallest(n, metric))[['user.uniqueId', metric]]
    # Reset index
    top_data = top_data.reset_index(drop=True)
    return top_data


# Hàm vẽ barchart
@st.cache_data
def create_bar_chart(data: pd.DataFrame, metric: str,
                     color_scale: str, y_label: str) -> go.Figure:
    """ Tạo biểu đồ cột cho người dùng hàng đầu """

    fig = px.bar(
        data,
        x='user.uniqueId',
        y=metric,
        color=metric,
        color_continuous_scale=color_scale,
        text=data[metric].apply(
            lambda x: f'{x:,.1f}' if metric == 'engagement_rate' else f'{x:,}'),
        height=450,
    )
    # Set min and max value for color scale
    fig.update_coloraxes(cmin=0, cmax=data[metric].max())
    fig.update_traces(
        # Add border to each bar
        marker_line_color='black',
        marker_line_width=1.5, opacity=0.8,
        # Change text position to outside of the bar
        # and color
        textposition='outside', textfont_size=12,
        textfont_color='black',
    )
    fig.update_layout(
        xaxis_title="ID của người dùng",
        yaxis_title=y_label,
        template="plotly_white",
        xaxis_tickangle=-30,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",

        # Tăng kích thước của các tiêu đề trục
        xaxis_title_font=dict(size=14, color=DARK_GRAY),
        yaxis_title_font=dict(size=14, color=DARK_GRAY),
    )
    # Ẩn colorbar ở bên phải
    fig.update_coloraxes(showscale=False)

    return fig


# Vẽ biểu bồ piechart thể hiện phân phối
# trong nhóm N người dùng được chọn
@st.cache_data
def create_pie_chart(data: pd.DataFrame, metric: str) -> go.Figure:
    """ Tạo biểu đồ tròn cho người dùng hàng đầu """

    fig = px.pie(
        data,
        names='user.uniqueId',
        values=metric,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=450,
    )
    # Set the pie chart lies on left side of the page
    # and the legend lies on right side of the page
    fig.update_layout(
        legend=dict(
            orientation="h",
            xanchor="center",
            yanchor="bottom",
            y=1.02,
            x=0.5,
            font=dict(size=12, color=DARK_GRAY),
        ),
    )
    fig.update_traces(textinfo='percent+label',
                      pull=[0.1] + [0]*(len(data)-1))
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        # Move chart to the bottom of the page
        margin=dict(t=80, b=0, l=0, r=0),
    )

    return fig


# ================================================================
# *_______________________ [Basic setup] ________________________*
# ================================================================
# Cấu hình Streamlit
st.set_page_config(
    page_title="Top User Analysis",
    page_icon="📊",
    layout="wide",
)
# Tiêu đề trang
st.markdown(
    '<div class="main-title" style="font-size: 48px; font-weight: bold; color: #1E90FF;">🏆 Phân tích những người dùng hàng đầu</div>',
    unsafe_allow_html=True
)
st.write("Khám phá những người dùng hoạt động hàng đầu dựa trên các chỉ số tương tác như lượt thích và số lượng video.")
st.divider()


# ================================================================
# *_______________ [Read data and set up styles] ________________*
# ================================================================
# Tải dữ liệu đã lưu trữ
df = load_user_data()


# ================================================================
# *___________________ [Data transformation] ____________________*
# ================================================================
# Tính tỷ lệ tương tác
df = calculate_engagement_ratio(df)


# ================================================================
# *_________________ [UI for selecting filters] _________________*
# ================================================================
st.header("Chọn bộ lọc để phân tích")
st.write("Chọn số lượng người dùng hàng đầu và loại biểu đồ để phân tích.")

# Tạo 3 cột để chọn các bộ lọc
filter_col1, filter_col2, filter_col3 = st.columns(
    spec=[4, 4, 2], gap="medium", border=True)
with filter_col1:
    top_n = st.slider(
        label="Chọn số lượng $N$ người dùng hàng đầu",
        min_value=1, max_value=50, value=10, step=1,
        help="Chọn số lượng người dùng hàng đầu để phân tích."
    )
with filter_col2:
    chart_option = st.selectbox(
        label="Chọn loại chỉ số",
        options=list(CHART_OPTIONS.keys())
    )
with filter_col3:
    sort_order = st.radio(
        label="Thứ tự sắp xếp",
        options=["Giảm dần", "Tăng dần"],
        index=0
    )


# ================================================================
# *________________ [Filter and visualize data] _________________*
# ================================================================
# Lọc dữ liệu theo các bộ lọc đã chọn
metric, color_scale, y_label = CHART_OPTIONS[chart_option]
top_data = filter_top_n_users(df=df, metric=metric,
                              n=top_n, sort_order=sort_order)

# Tạo 2 cột để hiển thị biểu đồ
barchart_col, piechart_col = st.columns(
    spec=[5, 5], gap="small", vertical_alignment="top", border=True)
with barchart_col:
    # Tạo tiêu đề cho biểu đồ
    sort_order_label: str = "cao nhất" if sort_order == "Giảm dần" else "thấp nhất"
    barchart_title: str = f"Top {top_n} người dùng với {chart_option} {sort_order_label}"
    st.subheader(barchart_title)

    # Vẽ biểu đồ cột
    bar_fig = create_bar_chart(
        data=top_data, metric=metric,
        color_scale=color_scale, y_label=y_label,
    )
    st.plotly_chart(bar_fig, use_container_width=True)
with piechart_col:
    # Tạo tiêu đề cho biểu đồ
    piechart_title: str = f"Phân phối của {chart_option} trong top {top_n} người dùng tương ứng"
    st.subheader(piechart_title)

    # Vẽ biểu đồ tròn
    pie_fig = create_pie_chart(data=top_data, metric=metric)
    st.plotly_chart(pie_fig, use_container_width=True)


# Dùng AI để rút ra insights từ biểu đồ
correlation_analysis_prompt = f"""
Hãy giúp tôi viết 1 đoạn nhận xét về phân bố của {barchart_title} và {piechart_title}. Đoạn nhận xét này nên ngắn gọn, xúc tích, tập trung vào những điểm nổi bật từ phân phối quan sát được. Đoạn văn chỉ nên có khoảng 350 đến 500 từ.

Tôi sẽ cung cấp cho bạn 3 thông tin về dữ liệu mà tôi đã phân tích.
Đầu tiên là một biểu đồ cột thể hiện giá trị {chart_option} của {top_n} người dùng được chọn. Màu sắc của cột càng đậm thì giá trị {chart_option} càng cao. Biểu đồ này sẽ được đính kèm dưới dạng byte:
{bar_fig.to_image()}

Thứ hai là một biểu đồ tròn thể hiện phân phối của {chart_option} trong nhóm {top_n} người dùng được chọn. Màu sắc của các phần trong biểu đồ tròn tương ứng với các người dùng khác nhau. Biểu đồ cũng cho biết tỷ lệ phần trăm của mỗi người dùng trong tổng số {top_n} người dùng. Biểu đồ này sẽ được đính kèm dưới dạng byte:
{pie_fig.to_image()}

Thứ ba là bảng thống kê chứa giá trị {chart_option} của {top_n} người dùng được chọn. Dưới đây là bảng thống kê thể hiện các thông tin này dưới dạng LaTeX:
{top_data[["user.uniqueId", metric]].to_latex()}

Đừng bắt đầu câu trả lời bằng các cụm từ như: "Dựa trên ..." mà hãy trực tiếp đi vào nội dung nhận xét. Đừng dùng các cụm từ như: "Bảng dữ liệu", "Bảng LaTeX", ...
"""
# print(top_data[["user.uniqueId", metric]])
display_AI_generated_insights(
    prompt=correlation_analysis_prompt,
    api_key="REDACTED_IN_ENV")


# Dữ liệu chi tiết
with st.expander(label=":blue[**Xem dữ liệu chi tiết**]", expanded=False):
    st.dataframe(
        top_data.style.format(
            {metric: "{:,.2f}" if metric == 'engagement_rate' else "{:,}"}),
        use_container_width=True
    )


# ================================================================
# *______________________ [Download data] _______________________*
# ================================================================
st.divider()
st.header("Tải dữ liệu")

st.write("Tải dữ liệu đã phân tích dưới dạng tệp CSV để sử dụng sau này.")
# Tùy chọn tải xuống
csv = top_data.to_csv(index=False)
st.download_button(
    label="**📥 Tải dữ liệu dưới dạng CSV**",
    data=csv,
    file_name=f"top_{top_n}_{chart_option.lower().replace(' ', '_')}_{sort_order.lower()}.csv",
    mime="text/plain",
    help="Nhấp vào đây để tải dữ liệu đã phân tích dưới dạng tệp CSV.",
    on_click="ignore",
    type="primary",
)
