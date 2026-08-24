"""
AI Service — Lost & Found AI

Cung cap hai mo hinh so khop chay song song:

  hybrid-text-v1 : Jaccard + Ratcliff-Obershelp + doi sanh thuoc tinh.
                   Khong can huan luyen, khong phu thuoc ngu lieu.

  tfidf-svd-v2   : TF-IDF + TruncatedSVD (Latent Semantic Analysis) +
                   doi sanh thuoc tinh. Hoc bieu dien an tu ngu lieu,
                   nho do bat duoc quan he dong nghia ma v1 bo sot.

Mo hinh v2 duoc nap LUOI (chi khi lan dau can dung) va co co che suy
giam nhe nhang: neu thieu artifact hoac thieu thu vien, service van chay
binh thuong voi v1 thay vi sap.
"""

from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal, Optional
import os
import re

from fastapi import FastAPI
from pydantic import BaseModel

MODEL_PATH = os.getenv("LSA_MODEL_PATH", "/app/model/lsa_model.joblib")
DEFAULT_MODEL = os.getenv("AI_MODEL", "tfidf-svd-v2")

app = FastAPI(title="Lost & Found AI Service", version="2.0")

# ---------------------------------------------------------------------
# Nap mo hinh LSA theo kieu luoi
# ---------------------------------------------------------------------
_lsa = None
_lsa_state = "chua nap"


def get_lsa():
    """Tra ve pipeline LSA, hoac None neu khong dung duoc."""
    global _lsa, _lsa_state
    if _lsa is not None or _lsa_state.startswith("loi"):
        return _lsa
    try:
        import joblib
        if not Path(MODEL_PATH).exists():
            _lsa_state = f"loi: khong tim thay {MODEL_PATH}"
            return None
        bundle = joblib.load(MODEL_PATH)
        _lsa = bundle["lsa"]
        _lsa_state = (f"da nap ({bundle.get('n_docs','?')} tai lieu, "
                      f"{bundle.get('n_components','?')} chieu)")
    except Exception as e:                      # thieu thu vien, file hong...
        _lsa_state = f"loi: {type(e).__name__}: {e}"
        _lsa = None
    return _lsa


# ---------------------------------------------------------------------
# Cau truc du lieu
# ---------------------------------------------------------------------
class PostFeature(BaseModel):
    title: str = ""
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    category_id: Optional[int] = None


class SimilarityRequest(BaseModel):
    lost: PostFeature
    found: PostFeature
    model: Optional[Literal["hybrid-text-v1", "tfidf-svd-v2"]] = None


# ---------------------------------------------------------------------
# Ham dung chung
# ---------------------------------------------------------------------
def norm(s: str) -> str:
    return " ".join(re.findall(r"\w+", (s or "").lower(), flags=re.UNICODE))


def long_text(p: PostFeature) -> str:
    return f"{p.title} {p.description} {p.color} {p.brand} {p.location}"


def token_jaccard(a: str, b: str) -> float:
    sa, sb = set(norm(a).split()), set(norm(b).split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def attr_signals(a: PostFeature, b: PostFeature):
    brand = 1.0 if a.brand and b.brand and norm(a.brand) == norm(b.brand) else 0.0
    color = 1.0 if a.color and b.color and norm(a.color) == norm(b.color) else 0.0
    cat = 1.0 if (a.category_id is not None and a.category_id == b.category_id) else 0.0
    return brand, color, cat


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------------
# Mo hinh 1: hybrid-text-v1
# ---------------------------------------------------------------------
def score_hybrid(a: PostFeature, b: PostFeature) -> dict:
    la, lb = long_text(a), long_text(b)
    j = token_jaccard(la, lb)
    seq = SequenceMatcher(None, norm(la), norm(lb)).ratio()
    brand, color, cat = attr_signals(a, b)
    total = clamp(0.40*j + 0.20*seq + 0.15*brand + 0.10*color + 0.15*cat)
    return {"similarity": round(total, 4), "model": "hybrid-text-v1",
            "components": {"jaccard": round(j, 4), "sequence": round(seq, 4),
                           "brand": brand, "color": color, "category": cat}}


# ---------------------------------------------------------------------
# Mo hinh 2: tfidf-svd-v2
# ---------------------------------------------------------------------
def score_lsa(a: PostFeature, b: PostFeature) -> dict:
    lsa = get_lsa()
    if lsa is None:                              # suy giam nhe nhang
        out = score_hybrid(a, b)
        out["model"] = "hybrid-text-v1"
        out["fallback"] = _lsa_state
        return out

    v = lsa.transform([norm(long_text(a)), norm(long_text(b))])
    cos = max(0.0, float(v[0] @ v[1]))
    brand, color, cat = attr_signals(a, b)
    total = clamp(0.60*cos + 0.15*brand + 0.10*color + 0.15*cat)
    return {"similarity": round(total, 4), "model": "tfidf-svd-v2",
            "components": {"cosine_lsa": round(cos, 4),
                           "brand": brand, "color": color, "category": cat}}


SCORERS = {"hybrid-text-v1": score_hybrid, "tfidf-svd-v2": score_lsa}


# ---------------------------------------------------------------------
# Cac diem cuoi
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "default_model": DEFAULT_MODEL,
            "available_models": list(SCORERS), "lsa_status": _lsa_state}


@app.post("/similarity")
def similarity(req: SimilarityRequest):
    """Cham diem bang mot mo hinh. Backend goi diem cuoi nay."""
    name = req.model or DEFAULT_MODEL
    return SCORERS.get(name, score_hybrid)(req.lost, req.found)


@app.post("/similarity/compare")
def compare(req: SimilarityRequest):
    """Cham diem bang CA HAI mo hinh — phuc vu do doi chung."""
    v1 = score_hybrid(req.lost, req.found)
    v2 = score_lsa(req.lost, req.found)
    return {"hybrid_text_v1": v1, "tfidf_svd_v2": v2,
            "delta": round(v2["similarity"] - v1["similarity"], 4)}
