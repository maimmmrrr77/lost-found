#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doi chung hai mo hinh so khop tren cung bo du lieu kiem thu.

  hybrid-text-v1 : Jaccard + Ratcliff-Obershelp + doi sanh thuoc tinh
  tfidf-svd-v2   : TF-IDF + TruncatedSVD (LSA) + doi sanh thuoc tinh

Chay:  python eval_compare.py     (can lsa_model.joblib da huan luyen)
"""

from difflib import SequenceMatcher
from itertools import product
import re

import joblib
import numpy as np

TH_V1 = 0.72     # nguong cua mo hinh tu vung
TH_V2 = 0.50     # nguong cua mo hinh LSA (thang diem khac nen nguong khac)

_lsa = joblib.load("lsa_model.joblib")["lsa"]


def norm(s):
    return " ".join(re.findall(r"\w+", s.lower(), flags=re.UNICODE))


def long_text(p):
    return f"{p['title']} {p['description']} {p['color']} {p['brand']} {p['location']}"


def attrs(a, b):
    brand = 1.0 if a["brand"] and b["brand"] and norm(a["brand"]) == norm(b["brand"]) else 0.0
    color = 1.0 if a["color"] and b["color"] and norm(a["color"]) == norm(b["color"]) else 0.0
    cat   = 1.0 if a["cat"] == b["cat"] else 0.0
    return brand, color, cat


def score_v1(a, b):
    la, lb = long_text(a), long_text(b)
    sa, sb = set(norm(la).split()), set(norm(lb).split())
    j   = len(sa & sb) / len(sa | sb) if (sa or sb) else 1.0
    seq = SequenceMatcher(None, norm(la), norm(lb)).ratio()
    br, co, ca = attrs(a, b)
    return max(0.0, min(1.0, 0.40*j + 0.20*seq + 0.15*br + 0.10*co + 0.15*ca))


def score_v2(a, b):
    v = _lsa.transform([norm(long_text(a)), norm(long_text(b))])
    cos = max(0.0, float(v[0] @ v[1]))
    br, co, ca = attrs(a, b)
    return max(0.0, min(1.0, 0.60*cos + 0.15*br + 0.10*co + 0.15*ca))


# ===================== BO DU LIEU (giong eval_matching.py) =====================

LOST = [
    dict(id='L1', cat=1, title='Mất iPhone 15 màu đen',
         description='Máy có ốp lưng trong suốt, xước nhẹ ở góc phải',
         color='Đen', brand='Apple', location='PTIT Hà Đông'),
    dict(id='L2', cat=2, title='Mất ví da màu nâu',
         description='Bên trong có căn cước công dân và thẻ ngân hàng',
         color='Nâu', brand='', location='Căng tin PTIT'),
    dict(id='L3', cat=3, title='Mất chùm chìa khóa xe máy',
         description='Chùm chìa khóa Honda có móc treo hình con gấu nhỏ màu nâu',
         color='Bạc', brand='Honda', location='Bãi gửi xe ký túc xá'),
    dict(id='L4', cat=4, title='Mất đồng hồ Casio đen',
         description='Đồng hồ điện tử dây nhựa, mặt vuông',
         color='Đen', brand='Casio', location='Sân bóng PTIT'),
    dict(id='L5', cat=5, title='Mất thẻ sinh viên',
         description='Thẻ sinh viên tên Nguyễn Văn An, mã B22DCCN001',
         color='', brand='', location='Thư viện PTIT'),
    dict(id='L6', cat=6, title='Mất laptop Dell XPS màu bạc',
         description='Máy có dán sticker hình mèo ở mặt lưng',
         color='Bạc', brand='Dell', location='Phòng học 2A15'),
]

FOUND = [
    dict(id='F1', cat=1, title='Nhặt được iPhone 15 màu đen tại PTIT',
         description='Điện thoại có ốp lưng trong suốt, góc phải bị xước nhẹ',
         color='Đen', brand='Apple', location='PTIT Hà Đông'),
    dict(id='F2', cat=2, title='Nhặt được một chiếc ví màu nâu',
         description='Trong ví có giấy tờ tùy thân và thẻ ATM',
         color='Nâu', brand='', location='Khu căng tin'),
    dict(id='F3', cat=3, title='Nhặt được chìa khóa có móc gấu bông',
         description='Chùm chìa khóa xe máy, móc treo hình chú gấu màu nâu',
         color='Bạc', brand='Honda', location='Nhà xe ký túc xá'),
    dict(id='F4', cat=4, title='Nhặt được đồng hồ đeo tay Casio',
         description='Đồng hồ điện tử màu đen, dây nhựa, mặt vuông',
         color='Đen', brand='Casio', location='Sân bóng'),
    dict(id='F5', cat=5, title='Nhặt được thẻ sinh viên Học viện Bưu chính',
         description='Thẻ mang tên Nguyễn Văn An, mã số B22DCCN001',
         color='', brand='', location='Tầng 2 thư viện'),
    dict(id='F6', cat=1, title='Nhặt được Samsung Galaxy S24 màu trắng',
         description='Máy còn mới, không ốp lưng',
         color='Trắng', brand='Samsung', location='Cổng trường'),
    dict(id='F7', cat=2, title='Nhặt được ví vải màu đen',
         description='Ví nhỏ đựng tiền lẻ, không có giấy tờ',
         color='Đen', brand='', location='Sân trường'),
    dict(id='F8', cat=4, title='Nhặt được đồng hồ Rolex mạ vàng',
         description='Đồng hồ cơ dây kim loại, mặt tròn',
         color='Vàng', brand='Rolex', location='Nhà gửi xe'),
]

TRUTH = {('L1','F1'), ('L2','F2'), ('L3','F3'), ('L4','F4'), ('L5','F5')}


def metrics(scorer, th):
    tp = fp = fn = 0
    for l, f in product(LOST, FOUND):
        if l['cat'] != f['cat']:          # buoc loc theo danh muc
            continue
        pred, act = scorer(l, f) >= th, (l['id'], f['id']) in TRUTH
        if pred and act:       tp += 1
        elif pred and not act: fp += 1
        elif not pred and act: fn += 1
    fn += sum(1 for l, f in product(LOST, FOUND)
              if l['cat'] != f['cat'] and (l['id'], f['id']) in TRUTH)
    p = tp/(tp+fp) if tp+fp else 0.0
    r = tp/(tp+fn) if tp+fn else 0.0
    return dict(tp=tp, fp=fp, fn=fn, p=p, r=r,
                f1=2*p*r/(p+r) if p+r else 0.0)


print("=" * 88)
print("BANG 1. DIEM SO TUNG CAP")
print("=" * 88)
print(f"{'Cap':<9}{'Loai':<14}{'hybrid-text-v1':>16}{'tfidf-svd-v2':>16}{'Chenh lech':>14}")
print("-" * 88)
for l, f in product(LOST, FOUND):
    if l['cat'] != f['cat']:
        continue
    pair = (l['id'], f['id'])
    s1, s2 = score_v1(l, f), score_v2(l, f)
    kind = 'cung do vat' if pair in TRUTH else 'khac do vat'
    m1 = 'v' if (s1 >= TH_V1) == (pair in TRUTH) else 'X'
    m2 = 'v' if (s2 >= TH_V2) == (pair in TRUTH) else 'X'
    print(f"{l['id']}-{f['id']:<6}{kind:<14}{s1:>14.4f} {m1}{s2:>14.4f} {m2}{s2-s1:>+14.4f}")

print()
print("=" * 88)
print("BANG 2. CHI SO TONG HOP")
print("=" * 88)
m1 = metrics(score_v1, TH_V1)
m2 = metrics(score_v2, TH_V2)
print(f"{'Mo hinh':<18}{'Nguong':>8}{'TP':>5}{'FP':>5}{'FN':>5}"
      f"{'Precision':>12}{'Recall':>10}{'F1':>10}")
print("-" * 88)
for name, th, m in [('hybrid-text-v1', TH_V1, m1), ('tfidf-svd-v2', TH_V2, m2)]:
    print(f"{name:<18}{th:>8.2f}{m['tp']:>5}{m['fp']:>5}{m['fn']:>5}"
          f"{m['p']:>12.4f}{m['r']:>10.4f}{m['f1']:>10.4f}")
print("-" * 88)
print(f"{'Cai thien':<18}{'':>8}{m2['tp']-m1['tp']:>+5}{m2['fp']-m1['fp']:>+5}"
      f"{m2['fn']-m1['fn']:>+5}{m2['p']-m1['p']:>+12.4f}"
      f"{m2['r']-m1['r']:>+10.4f}{m2['f1']-m1['f1']:>+10.4f}")

print()
print("=" * 88)
print("BANG 3. KHAO SAT NGUONG CHO tfidf-svd-v2")
print("=" * 88)
print(f"{'Nguong':>8}{'TP':>5}{'FP':>5}{'FN':>5}{'Precision':>12}{'Recall':>10}{'F1':>10}")
print("-" * 88)
best = None
for t in [0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80]:
    s = metrics(score_v2, t)
    print(f"{t:>8.2f}{s['tp']:>5}{s['fp']:>5}{s['fn']:>5}"
          f"{s['p']:>12.4f}{s['r']:>10.4f}{s['f1']:>10.4f}")
    if best is None or s['f1'] > best[1]['f1']:
        best = (t, s)
print("-" * 88)
print(f"F1 cao nhat tai nguong {best[0]:.2f}: F1={best[1]['f1']:.4f}  "
      f"P={best[1]['p']:.4f}  R={best[1]['r']:.4f}")
