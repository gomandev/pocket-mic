# PocketMic Audio Production Service

Backend service for AI-powered music production using open-source tools.

## Stack

- **MusicGen** (Meta) - Beat generation
- **Librosa** - Audio analysis
- **Essentia** - Musical feature extraction
- **Demucs** - Stem separation (coming soon)
- **FastAPI** - REST API
- **Supabase** - Storage & database

## Setup

### 1. Install Python 3.10+

```bash
python --version  # Should be 3.10 or higher
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will download ~1-2GB of models on first run.

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 5. Test installation

```bash
# Test MusicGen
python generate.py

# Test audio analysis
python analyze.py path/to/audio.wav
```

### 6. Run the service

```bash
python main.py
```

Service will be available at `http://localhost:8000`

## API Endpoints

### POST /process

Start audio production pipeline

```json
{
  "job_id": "uuid",
  "audio_url": "https://...",
  "blueprint": {
    "suggestedGenre": "Trap",
    "bpm": 140,
    "key": "C minor",
    "mood": "aggressive"
  }
}
```

### GET /health

Health check endpoint

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload --port 8000
```

## Deployment

Deploy to Railway, Render, or any Python hosting platform.

**Requirements**:
- Python 3.10+
- 2GB RAM minimum
- 5GB storage for models
