# Replicate API Setup

Get your free API token:
1. Visit https://replicate.com
2. Sign up (free - 50 generations/month)
3. Go to Account → API Tokens
4. Copy your token

Add to `.env`:
```
REPLICATE_API_TOKEN=r8_your_token_here
```

Test:
```bash
.\venv\Scripts\python.exe generate_replicate.py
```
