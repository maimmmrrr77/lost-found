-- Bat buoc dat bang ma cho ket noi truoc khi chen du lieu tieng Viet.
-- Thieu dong nay, tien trinh khoi tao cua MySQL se doc nham UTF-8 thanh Latin-1.
SET NAMES utf8mb4;

USE lost_found_ai;

INSERT IGNORE INTO categories(id,name,description,status) VALUES
(1,'Điện thoại','Điện thoại di động và phụ kiện',1),
(2,'Ví','Ví tiền, ví thẻ',1),
(3,'Chìa khóa','Chìa khóa và móc khóa',1),
(4,'Đồng hồ','Đồng hồ đeo tay',1),
(5,'Giấy tờ','CCCD, bằng lái, thẻ sinh viên...',1),
(6,'Laptop','Máy tính xách tay',1),
(7,'Khác','Các loại đồ vật khác',1);

-- password: Admin@123
INSERT IGNORE INTO users(id,full_name,username,email,phone,password,role,status,created_at) VALUES
(1,'Quản trị hệ thống','admin','admin@example.com',NULL,'$2y$12$Jk/U0hfAKbeqSkUCPvcGze5POr.LtokXOJMMJwAIjth7sp8KkScm.','ADMIN',1,NOW());
