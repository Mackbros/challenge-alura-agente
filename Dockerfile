FROM python:3.11-slim

WORKDIR /app

RUN apt-get update -qq && apt-get install -y -qq curl

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

RUN python3 -c "import site; p=site.getsitepackages()[0]+'/faiss/loader.py'; s=open(p).read(); s=s.replace('def is_sve_supported():','def is_sve_supported():\n        return False'); open(p,'w').write(s)"

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

WORKDIR /app/app
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
