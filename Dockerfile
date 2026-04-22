FROM python:3.11-slim
WORKDIR /app
 
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    locales \
    && sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*
 
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8
 
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY backend/ .
 
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
