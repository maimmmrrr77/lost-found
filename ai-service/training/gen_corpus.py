#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh ngu lieu huan luyen cho mo hinh tfidf-svd-v2.

NGUYEN TAC THIET KE
-------------------
LSA (Latent Semantic Analysis) hoc duoc quan he dong nghia THONG QUA
NGU CANH DUNG CHUNG. Hai tu chi duoc dat gan nhau trong khong gian an
neu chung cung xuat hien ben canh nhung tu khac giong nhau.

Vi du: de mo hinh hieu "can cuoc cong dan" ~ "giay to tuy than", ngu lieu
phai chua nhieu tai lieu trong do CA HAI cum tu deu dung chung ngu canh
voi "vi", "the ngan hang", "ATM", "bang lai"...

Vi vay bo sinh nay khong tao van ban ngau nhien. Moi danh muc co cac
NHOM DONG NGHIA duoc dinh nghia tuong minh, va moi tai lieu chon ngau
nhien MOT bien the tu moi nhom. Qua hang tram tai lieu, cau truc dong
xuat hien se hinh thanh du de SVD trich ra duoc.
"""

import json
import random

random.seed(20260821)   # co dinh de ket qua lap lai duoc

# =====================================================================
#  NHOM DONG NGHIA  — moi tuple la cac cach noi khac nhau cua CUNG mot y
# =====================================================================

GIAY_TO      = ["căn cước công dân", "CCCD", "giấy tờ tùy thân",
                "chứng minh thư", "thẻ căn cước", "giấy tờ cá nhân"]
THE_NGAN_HANG= ["thẻ ngân hàng", "thẻ ATM", "thẻ tín dụng",
                "thẻ Vietcombank", "thẻ rút tiền"]
TIEN         = ["một ít tiền mặt", "vài trăm nghìn", "tiền lẻ", "tiền mặt"]

TRUONG       = ["PTIT", "Học viện Bưu chính", "Học viện Công nghệ Bưu chính Viễn thông",
                "trường Bưu chính", "Học viện"]
THE_SV       = ["thẻ sinh viên", "thẻ SV", "thẻ học viên", "thẻ ra vào trường"]

DIEN_THOAI   = ["điện thoại", "smartphone", "máy điện thoại", "di động", "máy"]
OP_LUNG      = ["ốp lưng trong suốt", "vỏ nhựa trong", "ốp silicon trong",
                "case trong suốt", "ốp lưng nhựa dẻo"]
XUOC         = ["xước nhẹ ở góc", "trầy nhẹ phần góc", "có vết xước nhỏ",
                "sứt nhẹ ở cạnh", "bị trầy xước"]

LAPTOP       = ["laptop", "máy tính xách tay", "máy tính laptop", "notebook"]
CAP_SACH     = ["ba lô", "cặp sách", "túi xách", "balo laptop"]

CHIA_KHOA    = ["chùm chìa khóa", "chìa khóa xe máy", "bộ chìa khóa", "xâu chìa khóa"]
MOC_TREO     = ["móc treo hình con gấu", "móc khóa gấu bông", "móc treo hình chú gấu",
                "móc khóa hình gấu nhỏ", "móc treo thú bông"]

DONG_HO      = ["đồng hồ", "đồng hồ đeo tay", "đồng hồ điện tử", "đồng hồ cơ"]
DAY_DEO      = ["dây nhựa", "dây da", "dây kim loại", "dây vải dù"]

VI           = ["ví", "ví da", "bóp", "ví tiền", "bóp da"]

TAI_NGHE     = ["tai nghe", "tai nghe không dây", "earbuds", "tai nghe bluetooth"]
KINH         = ["kính cận", "mắt kính", "kính thuốc", "gọng kính"]
AO           = ["áo khoác", "áo gió", "áo hoodie", "áo len"]
BINH_NUOC    = ["bình nước", "chai nước giữ nhiệt", "bình giữ nhiệt", "ly giữ nhiệt"]

# Dia diem — dung chung cho moi danh muc de tao lien ket ngu canh
DIA_DIEM = [
    "thư viện {t}", "căng tin {t}", "sân bóng {t}", "bãi gửi xe {t}",
    "ký túc xá {t}", "phòng học 2A15", "phòng học 3B02", "giảng đường A1",
    "cổng trường {t}", "hành lang tầng 2", "nhà xe {t}", "sân trường {t}",
    "khu tự học", "phòng thực hành máy tính", "quán trà đá trước cổng",
]

MAU = ["đen", "trắng", "xám", "bạc", "nâu", "xanh dương", "đỏ", "vàng", "hồng", "be"]

HANG_DT   = ["Apple", "Samsung", "Xiaomi", "Oppo", "Vivo", "Realme"]
HANG_LT   = ["Dell", "HP", "Asus", "Lenovo", "Acer", "MacBook"]
HANG_DH   = ["Casio", "Citizen", "Seiko", "Rolex", "Daniel Wellington"]
HANG_XE   = ["Honda", "Yamaha", "Suzuki", "Piaggio"]

MO_DAU_LOST  = ["Mất", "Đánh rơi", "Thất lạc", "Làm rơi", "Bị mất", "Để quên"]
MO_DAU_FOUND = ["Nhặt được", "Tìm thấy", "Có nhặt được", "Vừa nhặt được", "Ai làm rơi"]


def pick(*groups):
    return [random.choice(g) for g in groups]


def alias(group, p=0.35):
    """Voi xac suat p, tra ve HAI bien the cua cung mot nhom dat canh nhau.

    Day la mau chot: neu moi tai lieu chi chua dung MOT bien the, cac bien
    the tro thanh loai tru nhau va SVD se hoc chung thanh DOI NGHICH thay
    vi dong nghia. Cho chung dong xuat hien mot phan tao ra lien ket bac
    mot, keo chung lai gan nhau trong khong gian an.
    """
    a = random.choice(group)
    if random.random() < p:
        b = random.choice([x for x in group if x != a])
        return random.choice([f"{a} ({b})", f"{a} hay còn gọi {b}", f"{a}, {b}"])
    return a


def dia_diem():
    return random.choice(DIA_DIEM).format(t=random.choice(TRUONG))


# =====================================================================
#  BO SINH THEO TUNG DANH MUC
# =====================================================================

def gen_dien_thoai():
    dt = alias(DIEN_THOAI)
    op, xc = pick(OP_LUNG, XUOC)
    hang, mau, dd = random.choice(HANG_DT), random.choice(MAU), dia_diem()
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (1, hang, mau,
            f"{mo_dau} {dt} {hang} màu {mau}",
            f"{dt.capitalize()} có {op}, {xc}, để quên tại {dd}")


def gen_vi():
    vi   = alias(VI)
    gt   = alias(GIAY_TO)
    tnh  = alias(THE_NGAN_HANG)
    tien = random.choice(TIEN)
    mau, dd = random.choice(MAU), dia_diem()
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (2, "", mau,
            f"{mo_dau} {vi} màu {mau}",
            f"Bên trong {vi} có {gt}, {tnh} và {tien}, thất lạc ở {dd}")


def gen_chia_khoa():
    ck  = alias(CHIA_KHOA)
    moc = alias(MOC_TREO)
    hang, mau, dd = random.choice(HANG_XE), random.choice(MAU), dia_diem()
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (3, hang, mau,
            f"{mo_dau} {ck} xe {hang}",
            f"{ck.capitalize()} có {moc} màu {mau}, rơi ở {dd}")


def gen_dong_ho():
    dh  = alias(DONG_HO)
    day = random.choice(DAY_DEO)
    hang, mau, dd = random.choice(HANG_DH), random.choice(MAU), dia_diem()
    mat = random.choice(["mặt vuông", "mặt tròn", "mặt chữ nhật"])
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (4, hang, mau,
            f"{mo_dau} {dh} {hang} màu {mau}",
            f"{dh.capitalize()} {day}, {mat}, để quên tại {dd}")


def gen_giay_to():
    the    = alias(THE_SV)
    gt     = alias(GIAY_TO)
    truong = alias(TRUONG)
    ten = random.choice(["Nguyễn Văn An", "Trần Thị Bình", "Lê Minh Cường",
                         "Phạm Thu Hà", "Hoàng Đức Duy", "Vũ Ngọc Lan"])
    ma = f"B22DCCN{random.randint(100, 699):03d}"
    dd = dia_diem()
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    # Co chu y: nua so tai lieu nhac ca the SV lan giay to tuy than,
    # tao cau noi ngu canh giua hai nhom tu vung nay.
    them = f" kèm theo {gt}" if random.random() < 0.5 else ""
    return (5, "", "",
            f"{mo_dau} {the} {truong}",
            f"{the.capitalize()} mang tên {ten}, mã số {ma}{them}, thất lạc ở {dd}")


def gen_laptop():
    lt = alias(LAPTOP)
    cap = random.choice(CAP_SACH)
    hang, mau, dd = random.choice(HANG_LT), random.choice(MAU), dia_diem()
    dd_them = random.choice(["dán sticker hình mèo", "dán decal hoạt hình",
                             "có sticker ở mặt lưng", "vỏ máy dán hình"])
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (6, hang, mau,
            f"{mo_dau} {lt} {hang} màu {mau}",
            f"{lt.capitalize()} đựng trong {cap}, {dd_them}, để quên ở {dd}")


def gen_khac():
    do = random.choice([TAI_NGHE, KINH, AO, BINH_NUOC])
    vat = random.choice(do)
    mau, dd = random.choice(MAU), dia_diem()
    mo_dau = random.choice(MO_DAU_LOST + MO_DAU_FOUND)
    return (7, "", mau,
            f"{mo_dau} {vat} màu {mau}",
            f"{vat.capitalize()} bỏ quên tại {dd}, mong ai nhặt được liên hệ")


GENERATORS = [gen_dien_thoai, gen_vi, gen_chia_khoa,
              gen_dong_ho, gen_giay_to, gen_laptop, gen_khac]


def build(n_per_cat=200):
    docs = []
    for gen in GENERATORS:
        for _ in range(n_per_cat):
            cat, brand, color, title, desc = gen()
            docs.append({"category_id": cat, "brand": brand, "color": color,
                         "title": title, "description": desc})
    random.shuffle(docs)
    return docs


if __name__ == "__main__":
    docs = build()
    with open("corpus.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=1)

    print(f"Da sinh {len(docs)} tai lieu -> corpus.json")
    from collections import Counter
    for cat, n in sorted(Counter(d["category_id"] for d in docs).items()):
        print(f"  danh muc {cat}: {n} tai lieu")
    print("\nVi du:")
    for d in docs[:4]:
        print(f"  [{d['category_id']}] {d['title']}")
        print(f"      {d['description']}")
