from pathlib import Path
from typing import Literal, Optional, List
import os
import re
import numpy as np
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPVisionModelWithProjection

MODEL_PATH = os.getenv("LSA_MODEL_PATH", "/app/model/lsa_model.joblib")
MODEL_NAME = "multimodal-v1"

app = FastAPI(title="Lost & Found AI Service", version="2.0")

# ---------------------------------------------------------------------
# Khởi tạo mô hình CLIP cho trích xuất & so khớp đặc trưng ảnh
# ---------------------------------------------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
try:
    clip_model = CLIPVisionModelWithProjection.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
except Exception as e:
    clip_model = None
    clip_processor = None
    print(f"Lỗi khởi tạo CLIP: {e}")

# ---------------------------------------------------------------------
# Nạp mô hình LSA theo kiểu lười (Lazy loading)
# ---------------------------------------------------------------------
_lsa = None
_lsa_state = "chưa nạp"

def get_lsa():
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
        _lsa_state = f"da nap ({bundle.get('n_docs','?')} tai lieu, {bundle.get('n_components','?')} chieu)"
    except Exception as e:
        _lsa_state = f"loi: {type(e).__name__}: {e}"
        _lsa = None
    return _lsa

# ---------------------------------------------------------------------
# Cấu trúc dữ liệu (Pydantic Models)
# ---------------------------------------------------------------------
class PostFeature(BaseModel):
    title: str = ""
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    category_id: Optional[int] = None
    event_date: Optional[str] = None
    image_embedding: Optional[List[float]] = None

class ImageExtractRequest(BaseModel):
    image_path: str

class SimilarityRequest(BaseModel):
    lost: PostFeature
    found: PostFeature
    model: Literal["multimodal-v1"] = MODEL_NAME

# ---------------------------------------------------------------------
# Các hàm trợ giúp (Helper Functions)
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

def compute_space_time_score(a: PostFeature, b: PostFeature) -> float:
    if not a.event_date or not b.event_date:
        return 0.5
    try:
        dt_a = datetime.fromisoformat(a.event_date.replace("Z", ""))
        dt_b = datetime.fromisoformat(b.event_date.replace("Z", ""))
        days_diff = abs((dt_a - dt_b).days)
        return max(0.0, 1.0 - (days_diff / 30.0))
    except Exception:
        return 0.5

def compute_image_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> Optional[float]:
    if not vec1 or not vec2:
        return None
    try:
        v1, v2 = np.array(vec1), np.array(vec2)
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))
    except Exception:
        return None

def clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

# ---------------------------------------------------------------------
# Công thức so khớp tổng hợp mới
# ---------------------------------------------------------------------
def score_multimodal(a: PostFeature, b: PostFeature) -> dict:
    lsa = get_lsa()
    if lsa is not None:
        v = lsa.transform([norm(long_text(a)), norm(long_text(b))])
        s_text = max(0.0, float(v[0] @ v[1]))
    else:
        s_text = token_jaccard(long_text(a), long_text(b))

    brand, color, cat = attr_signals(a, b)
    s_attr = 0.40 * brand + 0.30 * color + 0.30 * cat
    s_st = compute_space_time_score(a, b)
    s_img = compute_image_similarity(a.image_embedding, b.image_embedding)

    if s_img is not None:
        w_img, w_text, w_attr, w_st = 0.35, 0.30, 0.20, 0.15
        total = w_img * s_img + w_text * s_text + w_attr * s_attr + w_st * s_st
    else:
        w_text, w_attr, w_st = 0.50, 0.30, 0.20
        total = w_text * s_text + w_attr * s_attr + w_st * s_st

    total = clamp(total)

    return {
        "similarity": round(total, 4),
        "model": "multimodal-v1",
        "has_image_matching": (s_img is not None),
        "components": {
            "text": round(s_text, 4),
            "attribute": round(s_attr, 4),
            "space_time": round(s_st, 4),
            "image": round(s_img, 4) if s_img is not None else None,
            "brand": brand,
            "color": color,
            "category": cat
        }
    }

# ---------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "default_model": MODEL_NAME,
        "clip_loaded": clip_model is not None,
        "available_models": [MODEL_NAME],
        "lsa_status": _lsa_state
    }

@app.post("/extract-image-feature")
def extract_image_feature(req: ImageExtractRequest):
    if clip_model is None or clip_processor is None:
        raise HTTPException(status_code=500, detail="Mô hình CLIP chưa được nạp")
    if not os.path.exists(req.image_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp ảnh")

    try:
        image = Image.open(req.image_path).convert("RGB")
        inputs = clip_processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            image_features = clip_model(**inputs).image_embeds
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        embedding = image_features.cpu().numpy()[0].tolist()
        return {"embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi trích xuất ảnh: {str(e)}")

@app.post("/similarity")
def similarity(req: SimilarityRequest):
    return score_multimodal(req.lost, req.found)