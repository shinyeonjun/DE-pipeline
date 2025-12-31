FROM python:3.11-slim

WORKDIR /app/data_collect

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY data_collect/ /app/data_collect/

CMD ["python", "data_collect.py"]
