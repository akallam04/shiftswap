FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
