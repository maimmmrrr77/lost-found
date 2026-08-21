# API MVP

Base URL: `/api`

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| POST | `/auth/register` | No | Đăng ký |
| POST | `/auth/login` | No | Đăng nhập, nhận JWT |
| GET | `/auth/me` | Yes | Hồ sơ hiện tại |
| GET | `/categories` | No | Danh mục đồ vật |
| GET | `/posts` | No | Tìm/lọc bài đăng |
| POST | `/posts` | Yes | Đăng Lost/Found |
| GET | `/posts/{id}` | No | Chi tiết bài |
| GET | `/posts/mine` | Yes | Bài của tôi |
| POST | `/posts/{id}/images` | Yes | Upload ảnh multipart field `image` |
| PATCH | `/posts/{id}/close` | Yes | Đóng bài |
| GET | `/matches/mine` | Yes | Danh sách AI match liên quan |
| PATCH | `/matches/{id}` | Yes | Xác nhận/từ chối match |
| GET | `/notifications` | Yes | Thông báo |
| PATCH | `/notifications/{id}/read` | Yes | Đánh dấu đã đọc |

Khi chủ bài `LOST` xác nhận match với trạng thái `CONFIRMED`, hệ thống tự động chuyển cả bài `LOST` và bài `FOUND` liên quan sang `CLOSED`. Chỉ chủ bài `LOST` được xác nhận; các bên liên quan vẫn có thể từ chối match.

## Ví dụ tạo bài

```json
{
  "category_id": 1,
  "post_type": "LOST",
  "title": "Mất iPhone 15 màu đen",
  "description": "Máy có ốp trong suốt, xước nhẹ góc phải",
  "color": "Đen",
  "brand": "Apple",
  "location": "PTIT Hà Đông",
  "event_date": "2026-08-11 12:30:00",
  "contact": "0900000000",
  "reward": 500000
}
```
