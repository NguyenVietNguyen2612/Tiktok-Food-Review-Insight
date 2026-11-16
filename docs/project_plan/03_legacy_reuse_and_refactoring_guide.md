# ♻️ Kiểm kê Tài nguyên Tái sử dụng từ Dự án Cũ & Hướng dẫn Nâng cấp (Refactoring Guide)

> [!NOTE]
> Thư mục [21KHDL-TikTok-Analytics](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics) hiện có sẵn **~1.5 GB dữ liệu đã qua xử lý** và toàn bộ khung mã nguồn từ đồ án trước. Việc tái sử dụng thông minh giúp nhóm tiết kiệm **60%–70% thời gian** để tập trung vào các công nghệ mới (`DuckDB`, `Prefect`, `Qdrant`, `Librosa`, `ABSA`, `Seeding Detection`).

---

## 1. Bảng Tổng hợp: Giữ lại gì – Nâng cấp gì – Bỏ gì?

| Thành phần trong Repo cũ | Đường dẫn file chính | Quyết định | Cách thức Thay đổi & Nâng cấp |
| :--- | :--- | :--- | :--- |
| **Dữ liệu Lịch sử (54.5k videos, 23.1k transcripts, 14.2k món ăn/địa điểm)** | • [data/processed/merged_data.csv](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/processed/merged_data.csv)<br>• [data/transcripts/](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/transcripts)<br>• [data/foods-and-locations/](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/foods-and-locations)<br>• [data/content_analysis/content_analysis_data.parquet](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/content_analysis/content_analysis_data.parquet) | ✅ **Giữ lại 100% làm Historical Data** | • Không xóa bỏ. Viết 1 script nạp thẳng toàn bộ vào `DuckDB` (làm dữ liệu nền quy mô lớn) và đánh chỉ mục vào `Qdrant`.<br>• Chỉ cần crawl bổ sung **~200–300 video mới năm 2026** có đầy đủ Audio `.mp3` + Comments. |
| **Bộ Crawler & Custom `TikTokApi`** | • [src/crawler/crawler.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/crawler/crawler.py)<br>• [src/crawler/TikTokApi/api/comment.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/crawler/TikTokApi/api/comment.py) | 🔧 **Giữ lại & Mở rộng** | • Giữ nguyên thư mục `src/crawler/TikTokApi` (đã tích hợp sẵn `stealth` và class `Comment`).<br>• Sửa hàm `extract_video_contents` trong [crawler.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/crawler/crawler.py) để chỉ tải audio (`.mp3`) bằng `yt-dlp` và gọi thêm `video.comments(count=50)`. |
| **Danh sách 35+ Gemini API Keys** | • [development/apis.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/development/apis.py) | 🔧 **Chuẩn hóa Bảo mật** | • Chuyển danh sách key vào file `.env` (thêm vào `.gitignore` để không lộ key trên GitHub).<br>• Viết class `KeyRotator` tự động đổi key khi gặp lỗi `429 Quota Exceeded`. |
| **Bộ Nhãn & JSON Schema Phân tích Phong cách Video** | • [src/app/scriptwriting/tools/config/label_schema.json](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/scriptwriting/tools/config/label_schema.json)<br>• [src/app/scriptwriting/tools/utils.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/scriptwriting/tools/utils.py) | 🔧 **Tái sử dụng & Mở rộng sang ABSA** | • Tận dụng các nhãn có sẵn (`tone_of_voice`, `pacing`, `hook_type`, `word_per_second`).<br>• Mở rộng schema JSON để trích xuất thêm **ABSA 4 khía cạnh** (`taste`, `price`, `hygiene`, `service`) và dấu hiệu quảng cáo (`is_sponsored_tone`). |
| **Các Jupyter Notebooks Tiền xử lý** | • [notebooks/02_DEP_01-Preprocess_video_data.ipynb](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/notebooks/02_DEP_01-Preprocess_video_data.ipynb)<br>• [notebooks/03_FE_01_01-Transcribe_audio_colab.ipynb](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/notebooks/03_FE_01_01-Transcribe_audio_colab.ipynb)<br>• [notebooks/03_FE_02_02-Explore_food_location_data.ipynb](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/notebooks/03_FE_02_02-Explore_food_location_data.ipynb) | 🔄 **Chuyển thành Prefect Pipeline** | • Trích xuất logic làm sạch dữ liệu, chuẩn hóa tên món ăn/địa điểm và hàm `download_youtube_audio` từ `.ipynb` sang các module Python trong `src/pipelines/` được điều phối bởi `Prefect`. |
| **Giao diện Streamlit & Hàm vẽ Biểu đồ Plotly cũ** | • [src/app/streamlit_app.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/streamlit_app.py)<br>• [src/app/video_analysis/utils/chart.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/video_analysis/utils/chart.py)<br>• [src/app/trend_analysis/pages/food_location_analysis.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/trend_analysis/pages/food_location_analysis.py) | ❌ **Loại bỏ UI Streamlit – Chỉ lấy Logic Thống kê** | • **Thiết kế mới hoàn toàn giao diện bằng `Next.js` (App Router, TypeScript, TailwindCSS, shadcn/ui)** kết hợp bộ công cụ **`ui-ux-pro-max`** để đạt chuẩn thẩm mỹ sản phẩm SaaS thực tế.<br>• Chỉ trích xuất lại các công thức tính toán thống kê (IQR, Welch's t-test, gom nhóm món ăn, prompt `generate_insights`) trong code cũ để đưa vào tầng Backend `FastAPI` + `DuckDB`. |

---

## 2. Chi tiết Cách Thay đổi từng Module Cụ thể

### A. Nâng cấp Crawler ([src/crawler/crawler.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/crawler/crawler.py))
Hiện tại dòng `54–80` và `102–104` trong [crawler.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/crawler/crawler.py) đang để `# TODO: EXTRACT VIDEO CONTENTS` và tải file `.mp4` nặng nề. Cách sửa:
1. **Đổi cấu hình `yt-dlp` sang chỉ tải Audio (`.mp3` 64kbps):**
   * Kết hợp code từ Cell 7 của [03_FE_01_01-Transcribe_audio_colab.ipynb](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/notebooks/03_FE_01_01-Transcribe_audio_colab.ipynb): dùng `'format': 'bestaudio/best'` giúp kích thước mỗi file giảm từ ~15MB xuống chỉ còn ~500KB.
2. **Bổ sung lấy Bình luận (Comments):**
   * Trong vòng lặp `async for video in user.videos(...)`, gọi thêm:
     ```python
     comments_data = []
     async for comment in video.comments(count=50):
         comments_data.append(comment.as_dict)
     video_data["comments_list"] = comments_data
     ```

### B. Nâng cấp Tầng Lưu trữ sang `DuckDB` (Thay vì đọc trực tiếp hàng chục file CSV/JSON)
Hiện tại ứng dụng Streamlit đang đọc trực tiếp từng file rời rạc (`pd.read_parquet(...)`), còn 23.122 file trong [data/transcripts/](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/transcripts) (lưu ý: một số file JSON có ký tự xuống dòng chưa escape cần đọc bằng `json.loads(text, strict=False)`) và 14.252 file trong [data/foods-and-locations/](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/foods-and-locations) chưa được gom vào một CSDL thống nhất.
* **Cách nâng cấp:**
  * Tạo 1 file `data/warehouse/tiktok_pulse.duckdb` gồm các bảng:
    1. `dim_users`: Từ [cleaned_user_info.parquet](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/processed/cleaned_user_info.parquet).
    2. `fact_videos`: Hợp nhất từ [cleaned_video_info.parquet](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/processed/cleaned_video_info.parquet), [content_analysis_data.parquet](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/data/content_analysis/content_analysis_data.parquet) và [final_location_food_data.parquet](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/trend_analysis/data/final_location_food_data.parquet).
    3. `fact_transcripts_segments`: Lưu transcript chia theo từng đoạn có `start_sec`, `end_sec` và đặc trưng âm học từ `Librosa` (`words_per_sec`, `pitch_std`, `rms_energy`).
    4. `fact_comments`: Lưu bình luận người dùng kèm nhãn `is_seeding`, `seeding_reason`, `sentiment` và `aspect`.
    5. `fact_absa_reviews`: Kết quả bóc tách khen/chê theo 4 khía cạnh từ cả Giọng nói (Voice) và Bình luận (Comments).

### C. Nâng cấp Tầng AI: Từ "Hỗ trợ Viết kịch bản" sang "Voice Prosody + ABSA + Hybrid RAG"
Trong [src/app/scriptwriting/tools/utils.py](file:///home/intern-nvnguyen1/Project/21KHDL-TikTok-Analytics/src/app/scriptwriting/tools/utils.py), nhóm cũ đã viết sẵn hàm tính `mean_word_per_second` và ước lượng `time_range` (`0:00-0:15`).
* **Cách nâng cấp:**
  * Thay vì ước lượng thời gian bằng phép chia trung bình, đối với các video mới (và video người dùng dán link trực tiếp), dùng **Whisper (`word_timestamps=True` / `segments`)** để lấy mốc giây thực tế của từng câu nói.
  * Kết hợp với `Librosa` để đo biến thiên giọng nói thật sự trên file âm thanh.
  * Đẩy toàn bộ transcript + food/location + comments đã lọc seeding vào **Qdrant** để tạo **Trợ lý RAG Hỏi đáp Quán ăn kèm Timestamp**.

