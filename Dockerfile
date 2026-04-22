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

# Patch: corrige locale hardcoded no erpbrasil 1.2.1
# A função formata_decimal chama locale.setlocale('pt_BR.UTF-8') sem fallback.
# Este patch substitui por uma tentativa em ordem: pt_BR.UTF-8 → pt_BR → C.UTF-8
RUN python3 - << 'PYEOF'
import erpbrasil.edoc.pdf.danfe_formata as m
import inspect

f = inspect.getfile(m)
src = open(f).read()

old = "    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')\n"
new = (
    "    for _loc in ['pt_BR.UTF-8', 'pt_BR', 'C.UTF-8', 'C']:\n"
    "        try:\n"
    "            locale.setlocale(locale.LC_ALL, _loc)\n"
    "            break\n"
    "        except locale.Error:\n"
    "            continue\n"
)

if old in src:
    open(f, 'w').write(src.replace(old, new))
    print("Patch erpbrasil aplicado:", f)
else:
    print("AVISO: linha alvo nao encontrada — erpbrasil pode ter sido atualizado")
PYEOF

COPY backend/ .

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
