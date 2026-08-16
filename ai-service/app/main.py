from __future__ import annotations
from difflib import SequenceMatcher
from fastapi import FastAPI
from pydantic import BaseModel
import re

app = FastAPI(title="Lost & Found AI Service", version="0.1.0")

class PostFeatures(BaseModel):
    title: str = ""
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    category_id: int | None = None

class PairRequest(BaseModel):
    lost: PostFeatures
    found: PostFeatures

def norm(s: str) -> str:
    return " ".join(re.findall(r"\w+", s.lower(), flags=re.UNICODE))

def token_jaccard(a: str, b: str) -> float:
    sa, sb = set(norm(a).split()), set(norm(b).split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def text_score(a: PostFeatures, b: PostFeatures) -> float:
    long_a = f"{a.title} {a.description} {a.color} {a.brand} {a.location}"
    long_b = f"{b.title} {b.description} {b.color} {b.brand} {b.location}"
    j = token_jaccard(long_a, long_b)
    seq = SequenceMatcher(None, norm(long_a), norm(long_b)).ratio()
    brand = 1.0 if a.brand and b.brand and norm(a.brand) == norm(b.brand) else 0.0
    color = 1.0 if a.color and b.color and norm(a.color) == norm(b.color) else 0.0
    category = 1.0 if a.category_id is not None and a.category_id == b.category_id else 0.0
    return max(0.0, min(1.0, 0.40*j + 0.20*seq + 0.15*brand + 0.10*color + 0.15*category))

@app.get("/health")
def health():
    return {"status": "ok", "model": "hybrid-text-v1"}

@app.post("/similarity")
def similarity(req: PairRequest):
    score = text_score(req.lost, req.found)
    return {"similarity": round(score, 4), "model": "hybrid-text-v1"}
