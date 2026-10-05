# Lost & Found

Khung dự án cho đề tài **Xây dựng hệ thống tìm kiếm đồ vật thất lạc ứng dụng AI so khớp thông tin**.

## Kiến trúc

- `frontend/`: HTML5 + CSS3 + Bootstrap + JavaScript.
- `backend/`: PHP REST API, PDO MySQL, JWT authentication.
- `database/`: schema và seed dữ liệu.
- `ai-service/`: Python FastAPI, tách độc lập để sinh embedding/tính độ tương đồng.
- `docs/`: tài liệu API và hướng dẫn phát triển.

## Chức năng MVP

- Đăng ký, đăng nhập, xem hồ sơ.
- Danh mục đồ vật.
- Đăng bài Lost/Found, danh sách, xem chi tiết, cập nhật trạng thái.
- Lưu nhiều ảnh cho bài đăng.
- Tìm kiếm theo từ khóa/bộ lọc.
- Gọi AI service để tính độ tương đồng và lưu `matches`.
- Thông báo cho người dùng khi có kết quả ghép phù hợp.
- Phân quyền `USER` / `ADMIN` ở mức nền tảng.

## Chạy nhanh bằng Docker

1. Sao chép `.env.example` thành `.env`.
2. Chạy `docker compose up --build`.
3. Frontend: `http://localhost:8080/`
4. Backend API: `http://localhost:8080/api`
5. AI service: `http://localhost:8001/docs`
6. MySQL: `localhost:3307`, database `lost_found_ai`.

Tài khoản seed admin: `admin@example.com` / `Admin@123`.

---

## Đánh giá Hiệu năng Mô hình AI (Evaluation Results)

Mô hình **`multimodal-v1`** tích hợp trọng số đa thức (Text, Attributes, Spatial-Temporal) và Vector đặc trưng hình ảnh từ **OpenAI CLIP (`clip-vit-base-patch32`)** đã được kiểm thử thực nghiệm trên tập dữ liệu gồm **500 cặp bài đăng** (250 cặp `Match` thực sự và 250 cặp `Non-Match`).

### 1. Kết quả kiểm thử theo Ngưỡng (Threshold Benchmark)

Hệ thống đã thực hiện đánh giá độc lập ở hai mức ngưỡng để tìm ra "điểm ngọt" (Optimal Threshold) cân bằng giữa khả năng phát hiện đồ vật và hạn chế cảnh báo rác:

| Chỉ số (Metric) | Ngưỡng 0.50 | Ngưỡng 0.60 (Lựa chọn tối ưu) | Mức độ cải thiện |
| :--- | :---: | :---: | :---: |
| **Accuracy** (Độ chính xác chung) | 77.20% | **84.60%** | 🟢 **+7.40%** |
| **Precision** (Lớp Match) | 68.68% | **79.32%** | 🟢 **+10.64%** |
| **Recall** (Lớp Match) | **100.00%** | **93.60%** | 🟡 -6.40% |
| **F1-Score** (Lớp Match) | 81.43% | **85.87%** | 🟢 **+4.44%** |
| **Recall** (Lớp Non-Match) | 54.00% | **75.60%** | 🟢 **+21.60%** |

### 2. Chi tiết báo cáo tại Ngưỡng Tối ưu (`AI_MATCH_THRESHOLD = 0.60`)

```text
========================================
 KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH MULTIMODAL-V1
========================================
Ngưỡng chấp nhận (Threshold) : 0.60
Accuracy (Độ chính xác chung) : 84.60%
Precision (Độ chuẩn xác)      : 79.32%
Recall (Độ nhạy / Bắt trúng)  : 93.60%
F1-Score                      : 85.87%
========================================

Báo cáo chi tiết:
               precision    recall  f1-score   support

Non-Match (0)       0.92      0.76      0.83       250
    Match (1)       0.79      0.94      0.86       250

     accuracy                           0.85       500
    macro avg       0.86      0.85      0.84       500
 weighted avg       0.86      0.85      0.84       500