FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sinh ngu lieu va huan luyen mo hinh NGAY LUC BUILD.
# Nho vay container luc chay khong can mang, khoi dong nhanh,
# va moi lan build lai deu cho ra mo hinh giong het (random_state co dinh).
COPY training/ ./training/
RUN cd training && python gen_corpus.py && python train_lsa.py \
    && mkdir -p /app/model && cp lsa_model.joblib /app/model/ \
    && cp corpus.json /app/model/

COPY app ./app
ENV LSA_MODEL_PATH=/app/model/lsa_model.joblib
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
