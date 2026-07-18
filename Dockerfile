FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update -qq && apt-get install -y -qq curl && \
    pip install --no-cache-dir -r requirements.txt && \
    python3 -c "
path = __import__('site').getsitepackages()[0] + '/faiss/loader.py'
with open(path) as f:
    src = f.read()
src = src.replace(
    'def is_sve_supported():',
    'def is_sve_supported():\n        return False'
)
with open(path, 'w') as f:
    f.write(src)
"

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

WORKDIR /app/app
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
