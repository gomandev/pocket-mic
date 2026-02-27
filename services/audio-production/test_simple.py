"""
Simplified Beat Generation using Hugging Face Pipeline
This approach handles model downloading more robustly
"""
import sys
from unittest.mock import MagicMock

# Mock xformers to avoid DLL conflicts
sys.modules['xformers'] = MagicMock()
sys.modules['xformers.ops'] = MagicMock()

print("🎵 Testing simplified music generation...")
print("\nAttempting to load MusicGen via Hugging Face pipelines...")

try:
    from transformers import pipeline
    import torch
    
    # Use a smaller model for testing
    print("📥 Loading model (this downloads ~300MB on first run)...")
    
    # MusicGen small via transformers pipeline
    generator = pipeline(
        "text-to-audio",
        model="facebook/musicgen-small",
        device=-1  # CPU
    )
    
    print("✅ Model loaded successfully!")
    
    # Generate a short test beat
    print("\n🎹 Generating 5-second test beat...")
    prompt = "Trap beat, 140 BPM, aggressive, heavy 808s"
    
    audio = generator(
        prompt,
        max_new_tokens=256,  # ~5 seconds
        do_sample=True
    )
    
    # Save the output
    import scipy.io.wavfile as wavfile
    import numpy as np
    
    sample_rate = generator.model.config.audio_encoder.sampling_rate
    audio_data = np.array(audio["audio"][0])
    
    wavfile.write("test_beat.wav", rate=sample_rate, data=audio_data)
    
    print(f"✅ Beat generated and saved to: test_beat.wav")
    print(f"   Sample rate: {sample_rate}Hz")
    print(f"   Duration: ~5 seconds")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nThis might be due to:")
    print("1. Slow/failed model download from HuggingFace")
    print("2. Network connectivity issues")
    print("3. Missing dependencies")
    print("\nLet's try an alternative approach...")
    
    # Alternative: Just verify audiocraft imports work
    try:
        from audiocraft.models import MusicGen
        print("\n✅ AudioCraft imports successfully!")
        print("   (Model download is the bottleneck, not the code)")
    except Exception as e2:
        print(f"\n❌ AudioCraft import also failed: {e2}")
