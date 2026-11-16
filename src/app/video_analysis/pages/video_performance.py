import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# from data_preprocessing import video_info_df as df
from google import genai


# ================================================================
# *_____________________ [Define constants] _____________________*
# ================================================================
# Constants
METRIC_LABELS = {
    "Lượt xem": "statsV2.playCount",
    "Lượt thích": "statsV2.diggCount",
    "Lượt bình luận": "statsV2.commentCount",
    "Lượt chia sẻ": "statsV2.shareCount"
}

DURATION_BINS = [0, 10, 30, 60, 90, 120, 180, 300, 600, float("inf")]
DURATION_LABELS = [
    "<10s", "10-30s", "30-60s", "60-90s",
    "90-120s", "2 phút", "3-5 phút", "5-10 phút", ">10 phút"
]


# ================================================================
# *____________________ [Utility functions] _____________________*
# ================================================================
# Initialize Gemini client (should use st.secrets in production)
@st.cache_resource
def get_genai_client() -> genai.Client:
    """Initialize and cache the Gemini client"""
    try:
        # Use secrets in production
        return genai.Client(api_key="REDACTED_IN_ENV")
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        return None


def format_metric_name(metric: str) -> str:
    """Convert raw metric names to user-friendly labels"""
    return metric.replace("statsV2.", "").replace("Count", "").title()


def categorize_video_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize videos into duration bins.

    Args:
        df: DataFrame containing video duration data

    Returns:
        DataFrame with added 'video_duration_category' column
    """
    try:
        df["video_duration_category"] = pd.cut(
            df["video.duration"],
            bins=DURATION_BINS,
            labels=DURATION_LABELS,
            right=False
        )
        return df
    except Exception as e:
        st.error(f"Error categorizing video duration: {e}")
        return df


@st.cache_data(show_spinner=False)
def generate_report(data_str: str, model_name: str = "gemini-2.0-flash-lite") -> str:
    """
    Generate an analytical report using Gemini API.

    Args:
        data_str: Data to analyze in string format
        model_name: Gemini model to use

    Returns:
        Generated report in Markdown format
    """
    try:
        prompt = f"""
        Bạn là một nhà phân tích dữ liệu chuyên nghiệp. Hãy viết một vài dòng về phân tích dữ liệu TikTok từ kết quả thống kê như sau:
        {data_str}
        
        Yêu cầu:
        - Viết bằng tiếng Việt, ngôn ngữ đơn giản, dễ hiểu
        - Giọng văn hấp dẫn, thú vị
        - Định dạng Markdown với tiêu đề rõ ràng
        - Bắt đầu bằng 1-2 câu tóm tắt về dữ liệu
        - Tiếp theo, bao gồm ít nhất 3 insight quan trọng, mỗi insight chứa trong 1 câu
        """

        client = get_genai_client()
        if not client:
            return "Không thể kết nối với dịch vụ phân tích."

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )
        return response.text if hasattr(response, "text") else "Không nhận được phản hồi từ hệ thống."
    except Exception as e:
        st.error(f"Lỗi khi tạo báo cáo: {e}")
        return ""


def create_duration_plot(df: pd.DataFrame, metric_col: str, metric_name: str, agg_type: str = "Trung bình") -> go.Figure:
    """
    Create a plot showing video duration vs selected metric with configurable aggregation

    Args:
        df: Processed DataFrame
        metric_col: Column name for the metric
        metric_name: Display name for the metric
        agg_type: Type of aggregation ("Trung bình", "Tổng", or "Trung vị")
    """
    try:
        # Determine aggregation function based on user selection
        if agg_type == "Trung bình":
            agg_func = "mean"
            y_title = f"Trung bình {metric_name}"
        elif agg_type == "Tổng":
            agg_func = "sum"
            y_title = f"Tổng {metric_name}"
        else:  # "Trung vị"
            agg_func = "median"
            y_title = f"Trung vị {metric_name}"

        duration_summary = df.groupby("video_duration_category", observed=False).agg(
            num_videos=("video.id", "count"),
            metric_value=(metric_col, agg_func)
        ).reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Bar chart for number of videos
        fig.add_trace(
            go.Bar(
                x=duration_summary["video_duration_category"],
                y=duration_summary["num_videos"],
                name="Số video",
                marker_color="#1f77b4",
                opacity=0.7
            ),
            secondary_y=False
        )

        # Line chart for the selected metric
        fig.add_trace(
            go.Scatter(
                x=duration_summary["video_duration_category"],
                y=duration_summary["metric_value"],
                name=y_title,
                mode="lines+markers",
                marker_color="#ff7f0e",
                line=dict(width=3)
            ),
            secondary_y=True
        )

        fig.update_layout(
            title=f"Thời lượng video vs. {y_title}",
            xaxis_title="Phân loại thời lượng video",
            yaxis_title="Số video",
            yaxis2_title=y_title,
            hovermode="x unified",
            template="plotly_white"
        )

        return fig
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ: {e}")
        return go.Figure()


def create_time_analysis_plot(df: pd.DataFrame, time_col: str, metric_col: str, metric_name: str, agg_type: str = "Trung bình") -> go.Figure:
    """
    Create time-based analysis plots with configurable aggregation

    Args:
        df: Processed DataFrame
        time_col: Column name for time dimension
        metric_col: Column name for the metric
        metric_name: Display name for the metric
        agg_type: Type of aggregation ("Trung bình", "Tổng", or "Trung vị")
    """
    try:
        # Determine aggregation function
        if agg_type == "Trung bình":
            agg_func = "mean"
            y_title = f"Trung bình {metric_name}"
        elif agg_type == "Tổng":
            agg_func = "sum"
            y_title = f"Tổng {metric_name}"
        else:  # "Trung vị"
            agg_func = "median"
            y_title = f"Trung vị {metric_name}"

        # Make a copy to avoid modifying the original dataframe
        plot_df = df.copy()

        # Handle day names conversion if needed
        if time_col == "posting_day":
            day_map = {
                'Monday': 'Thứ 2',
                'Tuesday': 'Thứ 3',
                'Wednesday': 'Thứ 4',
                'Thursday': 'Thứ 5',
                'Friday': 'Thứ 6',
                'Saturday': 'Thứ 7',
                'Sunday': 'Chủ nhật'
            }
            day_order = ['Thứ 2', 'Thứ 3', 'Thứ 4',
                         'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']

            plot_df[time_col] = plot_df[time_col].map(day_map)
            plot_df[time_col] = pd.Categorical(
                plot_df[time_col],
                categories=day_order,
                ordered=True
            )

        time_summary = plot_df.groupby(time_col, observed=False).agg(
            metric_value=(metric_col, agg_func),
            num_videos=("video.id", "count")
        ).reset_index()

        # Sort the dataframe by the time_col to ensure proper ordering
        time_summary = time_summary.sort_values(time_col)

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=time_summary[time_col],
                y=time_summary["num_videos"],
                name="Số video",
                marker_color="#2ca02c",
                opacity=0.6
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=time_summary[time_col],
                y=time_summary["metric_value"],
                name=y_title,
                mode="lines+markers",
                marker_color="#d62728",
                line=dict(width=3)
            ),
            secondary_y=True
        )

        # Customize layout for days of week
        if time_col == "posting_day":
            fig.update_layout(
                xaxis_title="Ngày trong tuần",
                xaxis=dict(
                    type='category',
                    categoryorder='array',
                    categoryarray=day_order
                )
            )
        elif time_col == "posting_hour":
            fig.update_layout(xaxis_title="Giờ đăng trong ngày")

        fig.update_layout(
            yaxis2_title=y_title,
            title=f"{'Giờ' if time_col == 'posting_hour' else 'Ngày'} đăng vs. {y_title}"
        )

        return fig
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ phân tích thời gian: {e}")
        return go.Figure()


def display_metric_summary(df: pd.DataFrame, metric_col: str) -> None:
    """
    Display key metric statistics in a visually appealing way.

    Args:
        df: DataFrame containing the data
        metric_col: Column name for the metric
    """
    try:
        col1, col2, col3, col4 = st.columns(
            spec=[3,2,3,2], gap="small", border=True)

        total = df[metric_col].sum()
        avg = df[metric_col].mean()
        max_val = df[metric_col].max()
        top_video = df.loc[df[metric_col].idxmax(
        ), "desc"] if not df.empty else ""

        col1.metric(label="Tổng", 
                    value=f"{total:,.0f}")
        col2.metric(label="Trung bình",
                    value=f"{avg:,.0f}")
        col3.metric(label="Cao nhất",
                    value=f"{max_val:,.0f}")

        with col4:
            st.write("**Video hàng đầu:**")
            st.caption(top_video[:50] +
                       "..." if top_video else "Không có dữ liệu")
    except Exception as e:
        st.error(f"Lỗi khi hiển thị thống kê: {e}")


def display_dashboard(df: pd.DataFrame) -> None:
    """
    Main function to display the TikTok analytics dashboard.

    Args:
        df: DataFrame containing the TikTok video data
    """

    # Pre-process data
    df = categorize_video_duration(df)
    df['posting_hour'] = df['createTime'].dt.hour
    df['posting_day'] = df['createTime'].dt.day_name()

    # Sidebar controls
    with st.sidebar:
        st.title("🎛️ Bộ lọc")
        metric_name = st.selectbox(
            "Chỉ số hiệu suất",
            list(METRIC_LABELS.keys()),
            index=0
        )
        metric_col = METRIC_LABELS[metric_name]

        # Add aggregation type selector
        agg_type = st.selectbox(
            "Loại tổng hợp",
            ["Trung bình", "Tổng", "Trung vị"],
            index=0
        )

        if st.button("📊 Tạo báo cáo tổng thể"):
            with st.spinner("Đang phân tích dữ liệu..."):
                report_data = df.describe().to_string()
                report = generate_report(report_data)
                st.session_state.full_report = report

    # Main content
    st.title("📊 TikTok Video Analytics Dashboard")
    st.markdown("Phân tích hiệu suất video TikTok theo các chỉ số tương tác")

    # Display full report if generated
    if "full_report" in st.session_state:
        with st.expander("📝 Báo cáo tổng thể", expanded=True):
            st.markdown(st.session_state.full_report)

    # Metric summary cards
    display_metric_summary(df, metric_col)

    # Main charts
    st.subheader(f"⏳ Thời lượng video vs. {metric_name}")
    fig = create_duration_plot(df, metric_col, metric_name, agg_type)
    st.plotly_chart(fig, use_container_width=True)

    # Generate report for this section
    with st.expander(f"📝 Báo cáo cho Thời lượng video", expanded=False):
        with st.spinner("Đang phân tích..."):
            if agg_type == "Trung bình":
                report_data = df.groupby("video_duration_category", observed=False)[
                    metric_col].mean().to_string()
            elif agg_type == "Tổng":
                report_data = df.groupby("video_duration_category", observed=False)[
                    metric_col].sum().to_string()
            else:  # "Trung vị"
                report_data = df.groupby("video_duration_category", observed=False)[
                    metric_col].median().to_string()

            report = generate_report(report_data)
            st.markdown(report)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"⏰ Giờ đăng vs. {metric_name}")
        fig = create_time_analysis_plot(
            df, "posting_hour", metric_col, metric_name, agg_type)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"📝 Báo cáo cho Giờ đăng", expanded=False):
            with st.spinner("Đang phân tích..."):
                # report_data = df.groupby("posting_hour", observed=False)[metric_col].describe().to_string()

                if agg_type == "Trung bình":
                    report_data = df.groupby("posting_hour", observed=False)[
                        metric_col].mean().to_string()
                elif agg_type == "Tổng":
                    report_data = df.groupby("posting_hour", observed=False)[
                        metric_col].sum().to_string()
                else:  # "Trung vị"
                    report_data = df.groupby("posting_hour", observed=False)[
                        metric_col].median().to_string()

                report = generate_report(report_data)
                st.markdown(report)

    # Second row of charts
    # col1, col2 = st.columns(2)
    with col2:
        st.subheader(f"📅 Ngày đăng vs. {metric_name}")
        fig = create_time_analysis_plot(
            df, "posting_day", metric_col, metric_name, agg_type)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"📝 Báo cáo cho Ngày đăng", expanded=False):
            with st.spinner("Đang phân tích..."):
                # report_data = df.groupby("posting_day", observed=False)[metric_col].describe().to_string()
                if agg_type == "Trung bình":
                    report_data = df.groupby("posting_day", observed=False)[
                        metric_col].mean().to_string()
                elif agg_type == "Tổng":
                    report_data = df.groupby("posting_day", observed=False)[
                        metric_col].sum().to_string()
                else:  # "Trung vị"
                    report_data = df.groupby("posting_day", observed=False)[
                        metric_col].median().to_string()

                report = generate_report(report_data)
                st.markdown(report)

    st.subheader("Top Video Hiệu Suất Cao")
    top_videos = df.nlargest(5, metric_col)[["desc", metric_col]]
    st.dataframe(
        top_videos.rename(columns={
            "desc": "Mô tả",
            metric_col: metric_name
        }),
        hide_index=True,
        use_container_width=True
    )

    # Data download
    st.sidebar.download_button(
        label="📥 Tải dữ liệu",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="tiktok_analytics.csv",
        mime="text/csv"
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load data from session state"""
    return pd.read_parquet("data/processed/cleaned_video_info.parquet")


# ================================================================
# *_______________________ [Basic setup] ________________________*
# ================================================================
# Cấu hình Streamlit
st.set_page_config(
    page_title="TikTok Analytics Dashboard",
    page_icon="🎬",
    layout="wide"
)


# ================================================================
# *________________________ [Read data] _________________________*
# ================================================================
# Get the cached data from session state
df = load_data()


# ================================================================
# *_______________ [Show dashboard and insights] ________________*
# ================================================================
display_dashboard(df)
