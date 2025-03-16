# Sử dụng image pandoc/latex làm base (có hỗ trợ Pandoc và LaTeX)
FROM pandoc/latex:latest

# Cài đặt Python3, pip và các gói cần thiết cho API server
RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép requirements.txt trước để tận dụng Docker cache
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Sao chép các file ứng dụng vào container
COPY app.py .
COPY docx-equation-fix.yaml .

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose cổng để API server lắng nghe
EXPOSE 8000

# Chạy server với gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 4
