-- =====================================================================
--  BỘ DỮ LIỆU DEMO CHO HỆ THỐNG LOST & FOUND AI
--  Gồm: 3 người dùng, 14 bài đăng (6 LOST + 8 FOUND), kết quả so khớp
--       và thông báo tương ứng.
--
--  Chạy bằng:
--    docker compose cp seed-demo.sql db:/tmp/demo.sql
--    docker compose exec db mysql --default-character-set=utf8mb4 \
--        -ulostfound -plostfound123 lost_found_ai -e "source /tmp/demo.sql"
--
--  MẬT KHẨU CHUNG CHO CẢ 3 TÀI KHOẢN: MatKhau123
--
--  LƯU Ý QUAN TRỌNG:
--  Chèn thẳng bằng SQL sẽ KHÔNG kích hoạt hàm runMatching() trong
--  PostController. Vì vậy phần matches và notifications bên dưới được
--  chèn thủ công, với điểm số lấy từ kết quả chạy thật của thuật toán
--  hybrid-text-v1. Nếu muốn AI chạy thật sự thì dùng seed-demo.ps1.
-- =====================================================================

SET NAMES utf8mb4;
USE lost_found_ai;

-- ---------------------------------------------------------------------
-- 0. Dọn dữ liệu demo cũ (an toàn khi chạy lại nhiều lần)
--    Chỉ xóa dải ID 101+ nên không đụng dữ liệu bạn tự tạo.
-- ---------------------------------------------------------------------
DELETE FROM notifications WHERE id BETWEEN 101 AND 199;
DELETE FROM matches       WHERE id BETWEEN 101 AND 199;
DELETE FROM images        WHERE post_id BETWEEN 101 AND 199;
DELETE FROM posts         WHERE id BETWEEN 101 AND 199;
DELETE FROM users         WHERE id BETWEEN 101 AND 199;

-- ---------------------------------------------------------------------
-- 1. NGƯỜI DÙNG   (mật khẩu: MatKhau123)
-- ---------------------------------------------------------------------
INSERT INTO users(id, full_name, username, email, phone, password, role, status, created_at) VALUES
(101, 'Nguyễn Văn An',  'nguyenvanan', 'an@example.com',    '0901000001',
 '$2y$12$hN9dkzVD.DFov63qFPaZMusnTDJmlFd/oPUW7XWLkMeFJNAy0DVDq', 'USER', 1, '2026-08-15 08:00:00'),
(102, 'Trần Thị Bình',  'tranthibinh', 'binh@example.com',  '0901000002',
 '$2y$12$czxYhG8GiM5VyaLTU/s.du..XmcTNC6rGdJYYarujI070sDF.d8Jq', 'USER', 1, '2026-08-15 09:30:00'),
(103, 'Lê Minh Cường',  'leminhcuong', 'cuong@example.com', '0901000003',
 '$2y$12$oE4/X0Oqcp8YzrvxHzqqQOzBphf/sbvxi344dZDNNDnSTU7bdhP7u', 'USER', 1, '2026-08-16 14:00:00');

-- ---------------------------------------------------------------------
-- 2. BÀI ĐĂNG LOST  (do Nguyễn Văn An đăng)
--    Danh mục: 1 Điện thoại | 2 Ví | 3 Chìa khóa | 4 Đồng hồ
--              5 Giấy tờ    | 6 Laptop | 7 Khác
-- ---------------------------------------------------------------------
INSERT INTO posts(id, user_id, category_id, post_type, title, description, color, brand, location, event_date, contact, reward, status, created_at) VALUES
(101, 101, 1, 'LOST', 'Mất iPhone 15 màu đen',
 'Máy có ốp lưng trong suốt, xước nhẹ ở góc phải',
 'Đen', 'Apple', 'PTIT Hà Đông',        '2026-08-20 08:30:00', '0901000001', 500000, 'OPEN', '2026-08-20 08:45:00'),

(102, 101, 2, 'LOST', 'Mất ví da màu nâu',
 'Bên trong có căn cước công dân và thẻ ngân hàng',
 'Nâu', '', 'Căng tin PTIT',             '2026-08-20 11:15:00', '0901000001', 200000, 'OPEN', '2026-08-20 11:30:00'),

(103, 101, 3, 'LOST', 'Mất chùm chìa khóa xe máy',
 'Chùm chìa khóa Honda có móc treo hình con gấu nhỏ màu nâu',
 'Bạc', 'Honda', 'Bãi gửi xe ký túc xá', '2026-08-19 17:40:00', '0901000001', 100000, 'OPEN', '2026-08-19 18:00:00'),

(104, 101, 4, 'LOST', 'Mất đồng hồ Casio đen',
 'Đồng hồ điện tử dây nhựa, mặt vuông',
 'Đen', 'Casio', 'Sân bóng PTIT',        '2026-08-18 16:00:00', '0901000001', 0,      'OPEN', '2026-08-18 16:20:00'),

(105, 101, 5, 'LOST', 'Mất thẻ sinh viên',
 'Thẻ sinh viên tên Nguyễn Văn An, mã B22DCCN001',
 '', '', 'Thư viện PTIT',                '2026-08-20 14:20:00', '0901000001', 0,      'OPEN', '2026-08-20 14:35:00'),

(106, 101, 6, 'LOST', 'Mất laptop Dell XPS màu bạc',
 'Máy có dán sticker hình mèo ở mặt lưng',
 'Bạc', 'Dell', 'Phòng học 2A15',        '2026-08-17 09:00:00', '0901000001', 2000000,'OPEN', '2026-08-17 09:30:00');

-- ---------------------------------------------------------------------
-- 3. BÀI ĐĂNG FOUND
--    ID 107-111: do Trần Thị Bình đăng, khớp với các bài LOST ở trên
--    ID 112-114: do Lê Minh Cường đăng, CÙNG danh mục nhưng KHÁC đồ vật
--                (dùng để kiểm tra mô hình có loại đúng nhiễu không)
-- ---------------------------------------------------------------------
INSERT INTO posts(id, user_id, category_id, post_type, title, description, color, brand, location, event_date, contact, reward, status, created_at) VALUES
(107, 102, 1, 'FOUND', 'Nhặt được iPhone 15 màu đen tại PTIT',
 'Điện thoại có ốp lưng trong suốt, góc phải bị xước nhẹ',
 'Đen', 'Apple', 'PTIT Hà Đông',         '2026-08-20 09:10:00', '0901000002', 0, 'OPEN', '2026-08-20 09:20:00'),

(108, 102, 2, 'FOUND', 'Nhặt được một chiếc ví màu nâu',
 'Trong ví có giấy tờ tùy thân và thẻ ATM',
 'Nâu', '', 'Khu căng tin',               '2026-08-20 12:00:00', '0901000002', 0, 'OPEN', '2026-08-20 12:10:00'),

(109, 102, 3, 'FOUND', 'Nhặt được chìa khóa có móc gấu bông',
 'Chùm chìa khóa xe máy, móc treo hình chú gấu màu nâu',
 'Bạc', 'Honda', 'Nhà xe ký túc xá',      '2026-08-19 18:05:00', '0901000002', 0, 'OPEN', '2026-08-19 18:15:00'),

(110, 102, 4, 'FOUND', 'Nhặt được đồng hồ đeo tay Casio',
 'Đồng hồ điện tử màu đen, dây nhựa, mặt vuông',
 'Đen', 'Casio', 'Sân bóng',              '2026-08-18 17:30:00', '0901000002', 0, 'OPEN', '2026-08-18 17:45:00'),

(111, 102, 5, 'FOUND', 'Nhặt được thẻ sinh viên Học viện Bưu chính',
 'Thẻ mang tên Nguyễn Văn An, mã số B22DCCN001',
 '', '', 'Tầng 2 thư viện',               '2026-08-20 15:00:00', '0901000002', 0, 'OPEN', '2026-08-20 15:10:00'),

(112, 103, 1, 'FOUND', 'Nhặt được Samsung Galaxy S24 màu trắng',
 'Máy còn mới, không ốp lưng',
 'Trắng', 'Samsung', 'Cổng trường',       '2026-08-20 10:00:00', '0901000003', 0, 'OPEN', '2026-08-20 10:15:00'),

(113, 103, 2, 'FOUND', 'Nhặt được ví vải màu đen',
 'Ví nhỏ đựng tiền lẻ, không có giấy tờ',
 'Đen', '', 'Sân trường',                 '2026-08-19 13:25:00', '0901000003', 0, 'OPEN', '2026-08-19 13:40:00'),

(114, 103, 4, 'FOUND', 'Nhặt được đồng hồ Rolex mạ vàng',
 'Đồng hồ cơ dây kim loại, mặt tròn',
 'Vàng', 'Rolex', 'Nhà gửi xe',           '2026-08-18 08:45:00', '0901000003', 0, 'OPEN', '2026-08-18 09:00:00');

-- ---------------------------------------------------------------------
-- 4. KẾT QUẢ SO KHỚP
--    Điểm số lấy từ kết quả chạy thật thuật toán hybrid-text-v1.
--    Ba cặp dưới đây vượt ngưỡng mặc định 0.72.
-- ---------------------------------------------------------------------
INSERT INTO matches(id, lost_post_id, found_post_id, similarity_score, ai_model, status, created_at) VALUES
(101, 104, 110, 0.8122, 'hybrid-text-v1', 'PENDING', '2026-08-18 17:45:01'),  -- Đồng hồ Casio
(102, 101, 107, 0.8074, 'hybrid-text-v1', 'PENDING', '2026-08-20 09:20:01'),  -- iPhone 15
(103, 103, 109, 0.7852, 'hybrid-text-v1', 'PENDING', '2026-08-19 18:15:01');  -- Chìa khóa

-- Hai cặp dưới đây là trùng khớp THẬT nhưng chỉ đạt ~0.49 nên bị bỏ sót
-- ở ngưỡng 0.72. Bỏ dấu chú thích nếu bạn hạ AI_MATCH_THRESHOLD xuống 0.45.
-- INSERT INTO matches(id, lost_post_id, found_post_id, similarity_score, ai_model, status, created_at) VALUES
-- (104, 102, 108, 0.4894, 'hybrid-text-v1', 'PENDING', '2026-08-20 12:10:01'),  -- Ví da nâu
-- (105, 105, 111, 0.4885, 'hybrid-text-v1', 'PENDING', '2026-08-20 15:10:01');  -- Thẻ sinh viên

-- ---------------------------------------------------------------------
-- 5. THÔNG BÁO
--    Mỗi cặp so khớp sinh 2 thông báo: một cho chủ bài LOST,
--    một cho chủ bài FOUND. Đúng như logic trong runMatching().
-- ---------------------------------------------------------------------
INSERT INTO notifications(id, user_id, title, content, is_read, created_at) VALUES
(101, 101, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 81.2%.', 0, '2026-08-18 17:45:01'),
(102, 102, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 81.2%.', 0, '2026-08-18 17:45:01'),
(103, 101, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 80.7%.', 0, '2026-08-20 09:20:01'),
(104, 102, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 80.7%.', 0, '2026-08-20 09:20:01'),
(105, 101, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 78.5%.', 0, '2026-08-19 18:15:01'),
(106, 102, 'Có đồ vật tương đồng', 'Hệ thống phát hiện một bài đăng có độ tương đồng 78.5%.', 1, '2026-08-19 18:15:01');

-- ---------------------------------------------------------------------
-- 6. KIỂM TRA KẾT QUẢ
-- ---------------------------------------------------------------------
SELECT '--- NGƯỜI DÙNG ---' AS '';
SELECT id, full_name, email, role, status FROM users ORDER BY id;

SELECT '--- SỐ BÀI ĐĂNG THEO LOẠI ---' AS '';
SELECT post_type, COUNT(*) AS so_bai FROM posts GROUP BY post_type;

SELECT '--- CÁC CẶP SO KHỚP ---' AS '';
SELECT m.id,
       ROUND(m.similarity_score * 100, 1) AS diem_phan_tram,
       lp.title AS bai_lost,
       fp.title AS bai_found,
       m.status
FROM matches m
JOIN posts lp ON lp.id = m.lost_post_id
JOIN posts fp ON fp.id = m.found_post_id
ORDER BY m.similarity_score DESC;
