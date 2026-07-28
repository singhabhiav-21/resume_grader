FROM python:3.11.15

WORKDIR /backend

COPY app/requirements.txt .

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/
ENV PYTHONPATH=/backend

RUN mkdir -p /app/disk_stor /app/chroma_db
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]