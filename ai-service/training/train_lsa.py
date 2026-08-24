#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Huan luyen mo hinh tfidf-svd-v2 va luu tri artifact.

TF-IDF     : bieu dien van ban thanh vector thua theo tan suat tu, co
             trong so nghich dao tan suat tai lieu.
TruncatedSVD: chieu vector thua xuong khong gian an it chieu (LSA). Day
             la buoc tao ra kha nang bat tu dong nghia: cac tu cung xuat
             hien trong ngu canh giong nhau se co toa do gan nhau.

Luu y ve tieng Viet: tu tieng Viet gom nhieu am tiet ("can cuoc cong dan"
= 4 tieng). Vi vay dung ngram_range=(1,2) de bat duoc cac cum hai tieng
nhu "can cuoc", "cuoc cong", "cong dan".
"""

import json
import re
import sys

import joblib
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

N_COMPONENTS = 80         # so chieu khong gian an
ARTIFACT     = "lsa_model.joblib"


def norm(s: str) -> str:
    """Giong het ham norm trong ai-service de bao dam nhat quan."""
    return " ".join(re.findall(r"\w+", s.lower(), flags=re.UNICODE))


def doc_text(d: dict) -> str:
    return norm(f"{d['title']} {d['description']} {d.get('color','')} {d.get('brand','')}")


def train(corpus_path: str = "corpus.json"):
    with open(corpus_path, encoding="utf-8") as f:
        docs = json.load(f)
    texts = [doc_text(d) for d in docs]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),      # bat cum hai tieng cho tieng Viet
        min_df=2,                # bo tu chi xuat hien 1 lan (nhieu)
        sublinear_tf=True,       # dung 1+log(tf) thay cho tf tho
    )
    svd  = TruncatedSVD(n_components=N_COMPONENTS, random_state=42)
    lsa  = make_pipeline(vectorizer, svd, Normalizer(copy=False))

    lsa.fit(texts)

    n_terms = len(vectorizer.vocabulary_)
    var     = svd.explained_variance_ratio_.sum()
    print(f"  Tai lieu huan luyen : {len(texts)}")
    print(f"  So dac trung TF-IDF : {n_terms}")
    print(f"  So chieu sau SVD    : {N_COMPONENTS}")
    print(f"  Phuong sai giai thich: {var:.1%}")

    joblib.dump({"lsa": lsa, "n_components": N_COMPONENTS,
                 "n_docs": len(texts), "n_terms": n_terms}, ARTIFACT)
    print(f"  Da luu -> {ARTIFACT}")
    return lsa


def cosine(lsa, a: str, b: str) -> float:
    v = lsa.transform([norm(a), norm(b)])
    return float(np.clip(v[0] @ v[1], 0.0, 1.0))


if __name__ == "__main__":
    print("=== HUAN LUYEN ===")
    lsa = train()

    print("\n=== KIEM CHUNG tren van ban day du ===")
    P = [
        ("Mất ví da màu nâu Bên trong có căn cước công dân và thẻ ngân hàng",
         "Nhặt được ví màu nâu Trong ví có giấy tờ tùy thân và thẻ ATM", "cung do vat"),
        ("Mất thẻ sinh viên tên Nguyễn Văn An mã B22DCCN001 Thư viện PTIT",
         "Nhặt được thẻ sinh viên Học viện Bưu chính mang tên Nguyễn Văn An", "cung do vat"),
        ("Mất iPhone 15 màu đen máy có ốp lưng trong suốt xước nhẹ góc phải",
         "Nhặt được điện thoại Apple màu đen có vỏ nhựa trong trầy nhẹ phần góc", "cung do vat"),
        ("Mất ví da màu nâu có căn cước công dân và thẻ ngân hàng",
         "Nhặt được ví vải màu đen đựng tiền lẻ không có giấy tờ", "khac do vat"),
        ("Mất iPhone 15 màu đen ốp lưng trong suốt",
         "Nhặt được Samsung Galaxy S24 màu trắng máy còn mới", "khac do vat"),
    ]
    for a, b, note in P:
        c = cosine(lsa, a, b)
        ok = "OK" if (note == "cung do vat") == (c > 0.35) else "??"
        print(f"  {ok}  cosine={c:.4f}  ({note})")
        print(f"      A: {a[:66]}")
        print(f"      B: {b[:66]}")
