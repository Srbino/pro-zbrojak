# syntax=docker/dockerfile:1
#
# Pro Zbroják — runtime image pro nasazení (Coolify na Proxmoxu / jakýkoli Docker host).
# Obsahuje bundlovaný obsah (data/questions.json + images/), takže po startu
# nic nestahuje. Uživatelská data (SQLite DB, exporty) žijí na volume /state.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    SHOW=false \
    PRO_ZBROJAK_STATE_DIR=/state

WORKDIR /app

# Nejdřív jen requirements — lepší cachování vrstev při změně kódu.
COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir -r requirements-runtime.txt

# Zdrojový kód + bundlovaný obsah (viz .dockerignore, co se vynechává).
COPY . .

# Adresář pro persistentní data (namontuje se sem volume).
RUN mkdir -p /state/data /state/exports
VOLUME ["/state"]

EXPOSE 8080

# Health-check míří na /healthz (app.py). Port čte z env, aby fungoval i po změně PORT.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8080'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/healthz',timeout=3).status==200 else 1)"

CMD ["python", "app.py"]
