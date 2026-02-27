import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_production_trigger():
    url = "http://localhost:8000/process"
    
    # Use a real or placeholder job ID
    job_id = "89a9486a-513c-446f-bd35-2a18612c66f2"
    # Use a real audio URL (you can get one from your Supabase dashboard)
    audio_url = "https://sarrvzphjkqbileukukf.supabase.co/storage/v1/object/public/audio-assets/raw-vocals/1769982786151.wav"
    
    payload = {
        "job_id": job_id,
        "audio_url": audio_url,
        "blueprint": {
            "genre": "Trap",
            "bpm": 140,
            "key": "C minor",
            "mood": "aggressive"
        }
    }
    
    print(f"🚀 Triggering production for job: {job_id}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_trigger()
