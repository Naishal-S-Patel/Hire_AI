FROM python:3.11-slim

# System deps for psycopg2, spacy, whisper/ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ffmpeg git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (Docker cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
