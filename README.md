# Lost & Found AI

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

> Đây là bộ khung MVP để nhóm phát triển tiếp, không phải bản production. Khi triển khai thật cần bổ sung CSRF/CORS chặt chẽ, rate limit, object storage, email verification, reset password, audit log và model AI thực tế.
