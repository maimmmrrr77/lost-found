#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nap bo du lieu demo vao he thong Lost & Found AI.

Chay BEN TRONG container ai-service (da co san Python 3.11), goi toi
service `web` qua mang noi bo cua Docker. Nho vay hoan toan khong phu
thuoc vao bang ma cua Windows.

Cach chay tu thu muc goc du an:
    docker compose cp seed_demo.py ai-service:/tmp/seed.py
    docker compose exec ai-service python /tmp/seed.py
"""

import json
import urllib.request
import urllib.error

BASE = "http://web/api"          # ten service trong docker-compose
PASSWORD = "MatKhau123"


def call(path, data=None, token=None):
    """Goi API. json.dumps mac dinh escape ky tu Unicode thanh \\uXXXX
    nen payload gui di la ASCII thuan -> mien nhiem voi moi van de bang ma."""
    url = BASE + path
    body = json.dumps(data).encode("ascii") if data is not None else None
    req = urllib.request.Request(url, data=body, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def ensure_user(full_name, username, email):
    try:
        call("/auth/register", {
            "full_name": full_name, "username": username,
            "email": email, "password": PASSWORD,
        })
        print("  [+] Da tao tai khoan", email)
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("  [=] Tai khoan", email, "da ton tai")
        else:
            raise
    r = call("/auth/login", {"identity": email, "password": PASSWORD})
    return r["data"]["token"]


# 1 Dien thoai | 2 Vi | 3 Chia khoa | 4 Dong ho | 5 Giay to | 6 Laptop | 7 Khac

LOST = [
    (1, "Mất iPhone 15 màu đen",
        "Máy có ốp lưng trong suốt, xước nhẹ ở góc phải",
        "Đen", "Apple", "PTIT Hà Đông", "2026-08-20 08:30:00"),
    (2, "Mất ví da màu nâu",
        "Bên trong có căn cước công dân và thẻ ngân hàng",
        "Nâu", "", "Căng tin PTIT", "2026-08-20 11:15:00"),
    (3, "Mất chùm chìa khóa xe máy",
        "Chùm chìa khóa Honda có móc treo hình con gấu nhỏ màu nâu",
        "Bạc", "Honda", "Bãi gửi xe ký túc xá", "2026-08-19 17:40:00"),
    (4, "Mất đồng hồ Casio đen",
        "Đồng hồ điện tử dây nhựa, mặt vuông",
        "Đen", "Casio", "Sân bóng PTIT", "2026-08-18 16:00:00"),
    (5, "Mất thẻ sinh viên",
        "Thẻ sinh viên tên Nguyễn Văn An, mã B22DCCN001",
        "", "", "Thư viện PTIT", "2026-08-20 14:20:00"),
    (6, "Mất laptop Dell XPS màu bạc",
        "Máy có dán sticker hình mèo ở mặt lưng",
        "Bạc", "Dell", "Phòng học 2A15", "2026-08-17 09:00:00"),
]

FOUND_B = [
    (1, "Nhặt được iPhone 15 màu đen tại PTIT",
        "Điện thoại có ốp lưng trong suốt, góc phải bị xước nhẹ",
        "Đen", "Apple", "PTIT Hà Đông", "2026-08-20 09:10:00"),
    (2, "Nhặt được một chiếc ví màu nâu",
        "Trong ví có giấy tờ tùy thân và thẻ ATM",
        "Nâu", "", "Khu căng tin", "2026-08-20 12:00:00"),
    (3, "Nhặt được chìa khóa có móc gấu bông",
        "Chùm chìa khóa xe máy, móc treo hình chú gấu màu nâu",
        "Bạc", "Honda", "Nhà xe ký túc xá", "2026-08-19 18:05:00"),
    (4, "Nhặt được đồng hồ đeo tay Casio",
        "Đồng hồ điện tử màu đen, dây nhựa, mặt vuông",
        "Đen", "Casio", "Sân bóng", "2026-08-18 17:30:00"),
    (5, "Nhặt được thẻ sinh viên Học viện Bưu chính",
        "Thẻ mang tên Nguyễn Văn An, mã số B22DCCN001",
        "", "", "Tầng 2 thư viện", "2026-08-20 15:00:00"),
]

FOUND_C = [   # cung danh muc nhung KHAC do vat -> kiem tra AI loai nhieu
    (1, "Nhặt được Samsung Galaxy S24 màu trắng",
        "Máy còn mới, không ốp lưng",
        "Trắng", "Samsung", "Cổng trường", "2026-08-20 10:00:00"),
    (2, "Nhặt được ví vải màu đen",
        "Ví nhỏ đựng tiền lẻ, không có giấy tờ",
        "Đen", "", "Sân trường", "2026-08-19 13:25:00"),
    (4, "Nhặt được đồng hồ Rolex mạ vàng",
        "Đồng hồ cơ dây kim loại, mặt tròn",
        "Vàng", "Rolex", "Nhà gửi xe", "2026-08-18 08:45:00"),
]


def post_all(rows, post_type, token, contact):
    for cat, title, desc, color, brand, loc, when in rows:
        r = call("/posts", {
            "category_id": cat, "post_type": post_type,
            "title": title, "description": desc,
            "color": color, "brand": brand,
            "location": loc, "event_date": when,
            "contact": contact, "reward": 0,
        }, token)
        print("  [+] {} #{}  {}".format(post_type, r["data"]["id"], title))


def main():
    print("\n=== BUOC 1: Tao tai khoan ===")
    tk_a = ensure_user("Nguyễn Văn An", "nguyenvanan", "an@example.com")
    tk_b = ensure_user("Trần Thị Bình", "tranthibinh", "binh@example.com")
    tk_c = ensure_user("Lê Minh Cường", "leminhcuong", "cuong@example.com")

    print("\n=== BUOC 2: An dang 6 bai LOST ===")
    post_all(LOST, "LOST", tk_a, "0901000001")

    print("\n=== BUOC 3: Binh dang 5 bai FOUND (kich hoat so khop AI) ===")
    post_all(FOUND_B, "FOUND", tk_b, "0901000002")

    print("\n=== BUOC 4: Cuong dang 3 bai FOUND gay nhieu ===")
    post_all(FOUND_C, "FOUND", tk_c, "0901000003")

    print("\n=== BUOC 5: Ket qua so khop do AI tinh ===")
    rows = call("/matches/mine", token=tk_a)["data"]
    if not rows:
        print("  Khong co cap nao vuot nguong.")
        print("  Kiem tra AI Service:  docker compose logs ai-service")
    else:
        print("  Tim thay {} cap:".format(len(rows)))
        for m in sorted(rows, key=lambda x: -float(x["similarity_score"])):
            print("   - {:5.1f}%  [{}]  <->  [{}]".format(
                float(m["similarity_score"]) * 100,
                m["lost_title"], m["found_title"]))

    print("\nXong. Dang nhap: an@example.com / " + PASSWORD)
    print("Mo muc 'Goi y AI' de xem ket qua.\n")


if __name__ == "__main__":
    main()
