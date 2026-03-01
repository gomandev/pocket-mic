FROM python:3.10-slim

# Install system dependencies required by pedalboard, librosa, soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway sets PORT env var dynamically
ENV PORT=8000
EXPOSE ${PORT}

# Use sh -c to evaluate the $PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
