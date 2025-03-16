FROM pandoc/core:3.4 AS pandoc-base

# Giai đoạn thứ hai: Xây dựng ứng dụng Flask
FROM python:3.9-slim

# Sao chép pandoc từ image pandoc/core
COPY --from=pandoc-base /usr/local/bin/pandoc /usr/local/bin/
COPY --from=pandoc-base /usr/local/share/pandoc /usr/local/share/pandoc

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY docx-equation-fix.yaml .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
