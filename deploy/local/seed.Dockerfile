FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir requests==2.32.5
COPY scale-imports/json/ scale-imports/json/
COPY scale-imports/huaxinyun-original/json/ scale-imports/huaxinyun-original/json/
COPY scale-imports/scripts/*.py scale-imports/scripts/
COPY deploy/local/seed-scales.py .
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "seed-scales.py"]
