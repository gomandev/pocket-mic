"""
Beat Generation Service using Meta's MusicGen
"""
import os
import sys

# Disable xformers completely (we're running on CPU without CUDA)
os.environ['XFORMERS_DISABLED'] = '1'
os.environ['XFORMERS_MORE_DETAILS'] = '0'

from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import torch
import os

# Global model cache
_model = None

def get_model():
    """Load model once and cache it"""
    global _model
    if _model is None:
        print("📥 Loading MusicGen model (this may take a minute on first run)...")
        _model = MusicGen.get_pretrained('facebook/musicgen-small')
        print("✅ Model loaded!")
    return _model

def generate_beat(
    genre: str,
    bpm: int,
    key: str,
    mood: str,
    duration: int = 30
) -> str:
    """
    Generate instrumental beat based on musical parameters
    
    Args:
        genre: Musical genre (e.g., "Trap", "LoFi", "Drill")
        bpm: Tempo in beats per minute
        key: Musical key (e.g., "C minor")
        mood: Emotional mood (e.g., "aggressive", "calm")
        duration: Length in seconds
    
    Returns:
        Path to generated WAV file
    """
    print(f"🎹 Generating {genre} beat...")
    print(f"  └─ BPM: {bpm}, Key: {key}, Mood: {mood}")
    
    model = get_model()
    
    # Configure generation parameters
    model.set_generation_params(
        duration=duration,
        temperature=1.0,      # Creativity level
        top_k=250,           # Diversity
        top_p=0.0,
        cfg_coef=3.0         # How closely to follow prompt
    )
    
    # Construct detailed prompt
    # MusicGen works best with descriptive, specific prompts
    prompt = f"""
Professional {genre} instrumental track.
Tempo: {bpm} BPM.
Musical key: {key}.
Mood: {mood}.
High quality production with clean drums, deep bass, and melodic elements.
No vocals, pure instrumental.
"""
    
    print(f"  └─ Prompt: {prompt.strip()}")
    
    # Generate
    print("  └─ Generating audio...")
    with torch.no_grad():  # Save memory
        wav = model.generate([prompt], progress=True)
    
    # Save to file
    output_path = "generated_beat"
    audio_write(
        output_path,
        wav[0].cpu(),
        model.sample_rate,
        strategy="loudness",  # Normalize loudness
        loudness_compressor=True
    )
    
    final_path = f"{output_path}.wav"
    print(f"✅ Beat generated: {final_path}")
    
    return final_path

if __name__ == "__main__":
    # Test generation
    test_params = {
        "genre": "Trap",
        "bpm": 140,
        "key": "C minor",
        "mood": "aggressive",
        "duration": 15  # Short test
    }
    
    result = generate_beat(**test_params)
    print(f"\n🎵 Test beat saved to: {result}")
