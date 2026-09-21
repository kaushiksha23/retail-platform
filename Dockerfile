FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .

EXPOSE 8081

RUN useradd --create-home --shell /usr/sbin/nologin appuser

USER appuser

HEALTHCHECK --interval=5s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health', timeout=2)" || exit 1

CMD ["python", "app.py"]