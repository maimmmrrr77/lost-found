FROM python:3.11-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    LSA_MODEL_PATH=/app/model/lsa_model.joblib

# 1. Cài đặt các gói hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài riêng PyTorch CPU trước để tận dụng cache và giảm tải RAM khi build
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# 3. Cài các thư viện còn lại trong requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Sinh ngữ liệu và huấn luyện mô hình LSA
COPY training/ ./training/
RUN cd training && python gen_corpus.py && python train_lsa.py \
    && mkdir -p /app/model \
    && cp lsa_model.joblib /app/model/ \
    && cp corpus.json /app/model/

# 5. Copy mã nguồn app
COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]