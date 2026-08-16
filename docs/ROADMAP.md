# Roadmap đề xuất

## Giai đoạn 1 – MVP nghiệp vụ
- Hoàn thiện Auth, Posts, Categories, Images, Notifications.
- Trang hồ sơ, bài đăng của tôi, trang chi tiết.
- Admin quản lý user/category/post.

## Giai đoạn 2 – AI thật
- Thay `hybrid-text-v1` bằng embedding đa phương thức, ví dụ CLIP/SigLIP cho ảnh + text embedding tiếng Việt.
- Lưu vector trong vector DB hoặc cột vector phù hợp thay vì chỉ `embedding_path`.
- Kết hợp điểm: image similarity + text semantic + category/color/brand/location/time.
- Đánh giá Precision@K, Recall@K, threshold matching.

## Giai đoạn 3 – Chất lượng và triển khai
- Object storage cho ảnh, signed URL.
- Email verification / forgot password.
- Rate limiting, audit log, validation, moderation.
- Test unit/integration/E2E, CI/CD, HTTPS, backup DB.
