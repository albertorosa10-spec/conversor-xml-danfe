FROM python:3.11
WORKDIR /app

# Instalação completa de dependências de sistema, LibreOffice e fontes
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libcairo2-dev \
    pkg-config \
    locales \
    libreoffice \
    fonts-liberation \
    fonts-dejavu \
    && sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Patch crítico para erpbrasil 1.2.1
COPY patch_erpbrasil.py .
RUN python3 patch_erpbrasil.py

COPY backend/ .

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
