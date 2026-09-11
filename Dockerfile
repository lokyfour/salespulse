FROM python:3.12-slim

# System dependencies for audio processing and pyannote
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY src/ ./src/
COPY config/ ./config/

# Audio storage directory
RUN mkdir -p /data/audio

# Non-root user for security
RUN useradd --create-home --shell /bin/bash salespulse \
    && chown -R salespulse:salespulse /app /data
USER salespulse

EXPOSE 8000

CMD ["uvicorn", "salespulse.api.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
