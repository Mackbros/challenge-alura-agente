FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update -qq && apt-get install -y -qq curl && \
    pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -name loader.py -path "*/faiss/*" -exec \
        sed -i 's/def is_sve_supported():/def is_sve_supported():\n    return False/' {} \;

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

WORKDIR /app/app
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
