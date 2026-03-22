FROM python:3.11-slim

WORKDIR /app

# System deps for PDF parsing
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    default-jre-headless \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs data/schedule/1 data/schedule/2 data/schedule/3 data/schedule/4

EXPOSE 8000

CMD ["python", "run.py"]
