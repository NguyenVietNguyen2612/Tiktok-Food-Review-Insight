# pages/hashtag_analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
# Make sure to add these imports at the top if not already present
from google import genai
# from data_preprocessing import video_info_df as df
# from datetime import datetime


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

METRIC_COLORS = {
    "statsV2.playCount": "Viridis",
    "statsV2.diggCount": "Blues",
    "statsV2.commentCount": "Greens",
    "statsV2.shareCount": "Reds"
}


# ================================================================
# *____________________ [Utility functions] _____________________*
# ================================================================
@st.cache_resource
def get_genai_client() -> genai.Client:
    """Initialize and cache the Gemini client"""
    try:
        return genai.Client(api_key="REDACTED_IN_ENV")
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        return None


@st.cache_data(show_spinner=False)
def generate_report(data_str: str, model_name: str = "gemini-2.0-flash-lite") -> str:
    """Generate an analytical report using Gemini API"""
    try:
        prompt = f"""
        Bạn là chuyên gia phân tích TikTok. Hãy phân tích dữ liệu sau bằng tiếng Việt:
        {data_str}
        
        Yêu cầu:
        - Ngôn ngữ tự nhiên, dễ hiểu
        - Tập trung vào insights thực tế
        - Định dạng Markdown rõ ràng
        - 3-4 điểm chính, mỗi điểm 1-2 câu
        - Có thể đề xuất chiến lược nếu phù hợp
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


def filter_data_by_hashtag(df, hashtag):
    """Filter dataframe to include videos with the specified hashtag (case-insensitive)."""
    return df[
        df["hashtags"].apply(
            lambda x: hashtag.lower() in [tag.lower() for tag in x]
            if isinstance(x, (list, np.ndarray))
            else False
        )
    ]


def get_hashtag_stats(df, hashtag, metric_col):
    """Calculate statistics for a specific hashtag"""
    hashtag_df = filter_data_by_hashtag(df, hashtag)

    if hashtag_df.empty:
        return None

    stats = {
        'total_videos': len(hashtag_df),
        'total_engagement': hashtag_df[metric_col].sum(),
        'avg_engagement': hashtag_df[metric_col].mean(),
        'median_engagement': hashtag_df[metric_col].median(),
        'max_engagement': hashtag_df[metric_col].max(),
        'min_engagement': hashtag_df[metric_col].min()
    }

    return stats


def plot_hashtag_performance_over_time(df, hashtag, metric_col, time_agg="Theo tháng"):
    """Plot performance of a hashtag over time"""
    metric_name = next(k for k, v in METRIC_LABELS.items() if v == metric_col)
    hashtag_df = filter_data_by_hashtag(df, hashtag)

    if time_agg == "Theo ngày":
        hashtag_df["time_group"] = hashtag_df["createTime"].dt.strftime(
            "%Y-%m-%d")
    elif time_agg == "Theo tuần":
        hashtag_df["time_group"] = hashtag_df["createTime"].dt.to_period(
            "W").dt.to_timestamp()
    else:  # Theo tháng
        hashtag_df["time_group"] = hashtag_df["createTime"].dt.to_period(
            "M").dt.to_timestamp()

    grouped = hashtag_df.groupby("time_group")[metric_col].sum().reset_index()

    fig = px.line(
        grouped,
        x="time_group",
        y=metric_col,
        title=f"Hiệu suất của #{hashtag} theo thời gian ({time_agg})",
        labels={
            "time_group": "Ngày",
            metric_col: metric_name
        },
        line_shape="spline"
    )

    # fig.add_trace(line_color=METRIC_COLORS.get(metric_col, "Viridis"),
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Thời gian",
        yaxis_title=metric_name
    )

    return fig


def plot_hashtag_co_occurrence(df, hashtag, top_n=10):
    """Plot most common co-occurring hashtags"""
    # Get all videos containing the target hashtag
    target_videos = df[
        df["hashtags"].apply(
            lambda x: hashtag.lower() in [tag.lower() for tag in x]
            if isinstance(x, (list, np.ndarray))
            else False
        )
    ]

    # Explode the hashtags and count co-occurrences
    co_occurring = target_videos.explode('hashtags')
    co_occurring_counts = co_occurring[co_occurring['hashtags'] != hashtag].groupby(
        'hashtags').size().reset_index(name='count')
    top_co_occurring = co_occurring_counts.nlargest(top_n, 'count')

    fig = px.bar(
        top_co_occurring,
        x='hashtags',
        y='count',
        title=f"Hashtag thường xuất hiện cùng #{hashtag}",
        labels={'hashtags': 'Hashtag', 'count': 'Số lần xuất hiện'},
        color='count',
        color_continuous_scale='Viridis'
    )

    fig.update_layout(
        xaxis_title="Hashtag",
        yaxis_title="Số lần xuất hiện cùng",
        coloraxis_showscale=False
    )

    return fig


def plot_hashtag_author_performance(df, hashtag, metric_col, top_n=10):
    """Plot top authors using this hashtag"""
    metric_name = next(k for k, v in METRIC_LABELS.items() if v == metric_col)
    hashtag_df = filter_data_by_hashtag(df, hashtag)

    author_stats = hashtag_df.groupby('author.uniqueId').agg(
        total_engagement=(metric_col, 'sum'),
        video_count=('video.id', 'count'),
        avg_engagement=(metric_col, 'mean')
    ).reset_index().nlargest(top_n, 'total_engagement')

    fig = px.bar(
        author_stats,
        x='author.uniqueId',
        y='total_engagement',
        title=f"Tác giả sử dụng #{hashtag} hiệu quả nhất",
        labels={
            'author.uniqueId': 'Tác giả',
            'total_engagement': f'Tổng {metric_name}',
            'video_count': 'Số video'
        },
        hover_data=['video_count', 'avg_engagement'],
        color='total_engagement',
        color_continuous_scale=METRIC_COLORS.get(metric_col, "Viridis")
    )

    fig.update_layout(
        xaxis_title="Tác giả",
        yaxis_title=f"Tổng {metric_name}",
        coloraxis_showscale=False
    )

    return fig


# Update the display_hashtag_analysis function in hashtag_analysis.py
def display_hashtag_analysis(df):
    """Display the hashtag analysis dashboard"""

    st.title("🔍 Phân Tích Hashtag Đơn Lẻ")

    # Get list of all unique hashtags
    all_hashtags = sorted(
        list(set([tag for sublist in df['hashtags'].dropna() for tag in sublist])))

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Cài Đặt Phân Tích")
        selected_hashtag = st.selectbox(
            label="Chọn hashtag để phân tích",
            options=all_hashtags,
            index=all_hashtags.index(
                'monngonmoingay') if 'monngonmoingay' in all_hashtags else 0
        )

        selected_metric = st.selectbox(
            "Chỉ số phân tích",
            list(METRIC_LABELS.keys()),
            index=0
        )
        metric_col = METRIC_LABELS[selected_metric]

        time_agg = st.selectbox(
            "Nhóm theo thời gian",
            ["Theo ngày", "Theo tuần", "Theo tháng"],
            index=2
        )

        top_n = st.slider(
            "Số lượng kết quả hiển thị",
            5, 20, 10
        )

        # Add report generation button
        if st.button("📊 Tạo báo cáo tổng thể"):
            with st.spinner("Đang phân tích dữ liệu..."):
                report_data = df.describe().to_string()
                report = generate_report(report_data)
                st.session_state.full_report = report

    # Display full report if generated
    if "full_report" in st.session_state:
        with st.expander("📝 Báo cáo tổng thể", expanded=True):
            st.markdown(st.session_state.full_report)

    # Main content
    st.header(f"Phân tích hiệu suất của #{selected_hashtag}")

    # Hashtag statistics cards
    stats = get_hashtag_stats(df, selected_hashtag, metric_col)

    if stats:
        col1, col2, col3, col4 = st.columns(
            spec=[2, 3, 2, 2], gap="small", border=True)
        col1.metric("Tổng video",
                    f"{int(stats['total_videos']):,}")
        col2.metric(f"Tổng {selected_metric}",
                    f"{int(stats['total_engagement']):,}")
        col3.metric(f"Trung bình {selected_metric}",
                    f"{stats['avg_engagement']:,.0f}")
        col4.metric(f"Trung vị {selected_metric}",
                    f"{stats['median_engagement']:,.0f}")

        # Performance over time
        st.subheader(f"Hiệu suất #{selected_hashtag} theo thời gian")
        st.plotly_chart(
            plot_hashtag_performance_over_time(
                df, selected_hashtag, metric_col, time_agg),
            use_container_width=True
        )

        # Co-occurring hashtags
        st.subheader(f"Hashtag thường đi cùng #{selected_hashtag}")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.plotly_chart(
                plot_hashtag_co_occurrence(df, selected_hashtag, top_n),
                use_container_width=True
            )

        with col2:
            # ":blue-background[:blue[**:material/auto_awesome: Nhận xét từ AI**]]"
            # st.markdown("### Nhận Xét AI")
            st.markdown(
                "#### :blue-background[:blue[**:material/auto_awesome: Nhận xét từ AI**]]")
            with st.expander(f"📝 Báo cáo cho Hashtag thường đi cùng #{selected_hashtag}"):
                with st.spinner("Đang phân tích hashtag liên quan..."):
                    # Get co-occurrence data
                    target_videos = df[df['hashtags'].apply(
                        lambda x: selected_hashtag in x if isinstance(x, list) else False)]
                    co_occurring = target_videos.explode('hashtags')
                    co_counts = co_occurring[co_occurring['hashtags'] !=
                                             selected_hashtag]['hashtags'].value_counts().head(top_n)

                    # Generate insights
                    chart_prompt = f"""
                    Phân tích hashtag liên quan cho #{selected_hashtag}:
                    - Tổng video: {stats['total_videos']}
                    - Các hashtag thường xuất hiện cùng:
                    {co_counts.to_string()}
                    
                    Hãy đưa ra 3-4 nhận xét ngắn gọn trong vòng 100 từ bằng tiếng Việt về:
                    1. Chủ đề chung của các hashtag liên quan
                    2. Mối quan hệ giữa các hashtag này với #{selected_hashtag}
                    3. Gợi ý cách kết hợp hashtag hiệu quả
                    """

                    insights = generate_report(chart_prompt)
                    st.markdown(insights)

            if st.button("🔄 Làm mới nhận xét", key="co_occurrence_insights"):
                st.rerun()

        # Top authors using this hashtag
        st.subheader(f"Tác giả sử dụng #{selected_hashtag} hiệu quả nhất")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.plotly_chart(
                plot_hashtag_author_performance(
                    df, selected_hashtag, metric_col, top_n),
                use_container_width=True
            )

        with col2:
            # st.markdown("### Nhận Xét")
            st.markdown(
                "#### :blue-background[:blue[**:material/auto_awesome: Nhận xét từ AI**]]")
            with st.expander(f"📝 Báo cáo cho Tác giả sử dụng #{selected_hashtag} hiệu quả nhất"):
                with st.spinner("Đang phân tích tác giả..."):
                    # Get top authors data
                    top_authors = df[
                        df["hashtags"].apply(
                            lambda x: selected_hashtag.lower() in [
                                tag.lower() for tag in x]
                            if isinstance(x, (list, np.ndarray))
                            else False
                        )
                    ]
                    author_stats = top_authors.groupby('author.uniqueId')[
                        metric_col].sum().nlargest(top_n)

                    # Generate insights
                    chart_prompt = f"""
                    Phân tích các tác giả (users) sử dụng #{selected_hashtag}:
                    - Số tác giả phân tích: {len(author_stats)}
                    - Tác giả hàng đầu: {author_stats.index[0]} với {author_stats.iloc[0]:,} {selected_metric}
                    - Tổng quan hiệu suất:
                    {author_stats.describe().to_string()}
                    
                    Hãy đưa ra 3-4 nhận xét ngắn gọn trong vòng 100 từ bằng tiếng Việt về:
                    1. Đặc điểm chung của các tác giả hiệu quả
                    2. Khoảng cách giữa tác giả hàng đầu và các tác giả khác
                    3. Gợi ý để cải thiện hiệu suất hashtag
                    """

                    insights = generate_report(chart_prompt)
                    st.markdown(insights)

            if st.button("🔄 Làm mới nhận xét", key="author_insights"):
                st.rerun()

        # Raw data
        with st.expander("Xem dữ liệu thô"):
            hashtag_data = filter_data_by_hashtag(df, selected_hashtag)
            st.dataframe(
                hashtag_data[['createTime', 'desc', metric_col, 'author.uniqueId', 'hashtags']].sort_values(
                    metric_col, ascending=False),
                use_container_width=True
            )
    else:
        st.warning(f"Không tìm thấy dữ liệu cho hashtag #{selected_hashtag}")


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load data from session state"""
    return pd.read_parquet("data/processed/cleaned_video_info.parquet")


# ================================================================
# *_______________________ [Basic setup] ________________________*
# ================================================================
# Cấu hình Streamlit
st.set_page_config(
    page_title="Single Hashtag Analysis",
    page_icon="📊",
    layout="wide",
)


# ================================================================
# *________________________ [Read data] _________________________*
# ================================================================
# Get the cached data from session state
df = load_data()


# ================================================================
# *_______________ [Show dashboard and insights] ________________*
# ================================================================
display_hashtag_analysis(df)
