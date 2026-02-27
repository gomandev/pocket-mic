"""
Audio Analysis Service
Analyzes uploaded vocals using Librosa and Essentia
"""
import librosa
import numpy as np
from pathlib import Path
import tempfile
import httpx

async def download_audio(url: str) -> str:
    """Download audio from Supabase to temp file"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name

def analyze_audio(audio_path: str) -> dict:
    """
    Analyze audio file and extract musical features
    Returns: BPM, key, mood, duration, sample_rate
    """
    print(f"🎵 Analyzing audio: {audio_path}")
    
    # Load audio with librosa
    y, sr = librosa.load(audio_path, sr=44100, mono=True)
    
    # 1. Tempo/BPM Detection
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    print(f"  └─ BPM: {int(tempo)}")
    
    # 2. Key Detection using Librosa chromagram
    try:
        # Extract chromagram for key detection
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Average over time to get key profile
        chroma_profile = np.mean(chroma, axis=1)
        
        # Key names
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Find strongest key
        key_idx = np.argmax(chroma_profile)
        detected_key = keys[key_idx]
        
        # Estimate major/minor by looking at 3rd interval
        third_interval = chroma_profile[(key_idx + 4) % 12]  # Major third
        minor_third = chroma_profile[(key_idx + 3) % 12]     # Minor third
        
        scale = "major" if third_interval > minor_third else "minor"
        detected_key_full = f"{detected_key} {scale}"
        strength = float(chroma_profile[key_idx])
        
        print(f"  └─ Key: {detected_key_full} (confidence: {strength:.2f})")
    except Exception as e:
        print(f"  └─ Key detection failed: {e}")
        detected_key_full = "C major"
        strength = 0.5
    
    # 3. Energy/Mood Analysis
    # RMS (loudness)
    rms = librosa.feature.rms(y=y)[0]
    avg_rms = float(np.mean(rms))
    
    # Spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    avg_centroid = float(np.mean(spectral_centroid))
    
    # Zero crossing rate (noisiness/rhythm)
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    avg_zcr = float(np.mean(zcr))
    
    # Mood classification
    if avg_rms > 0.05 and avg_centroid > 2000:
        mood = "energetic"
    elif avg_rms < 0.03:
        mood = "calm"
    elif avg_centroid < 1500:
        mood = "dark"
    else:
        mood = "balanced"
    
    print(f"  └─ Mood: {mood}")
    
    # 4. Duration
    duration = float(len(y) / sr)
    print(f"  └─ Duration: {duration:.2f}s")
    
    return {
        "bpm": int(tempo),
        "key": detected_key,
        "key_confidence": float(strength),
        "mood": mood,
        "energy": {
            "rms": avg_rms,
            "brightness": avg_centroid,
            "rhythm_complexity": avg_zcr
        },
        "duration": duration,
        "sample_rate": sr
    }

if __name__ == "__main__":
    # Test with a sample file
    import sys
    if len(sys.argv) > 1:
        result = analyze_audio(sys.argv[1])
        print("\n✅ Analysis complete!")
        print(result)
    else:
        print("Usage: python analyze.py <audio_file_path>")
