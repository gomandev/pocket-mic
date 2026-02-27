"""
Beat Generation using Stable Audio via Replicate API
Professional-grade instrumental generation with vocal DNA awareness
"""
import replicate
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()


def build_stable_audio_prompt(
    genre: str,
    bpm: int,
    key: str,
    mood: str,
    density_hints: dict = None,
    vocal_dna: dict = None
) -> str:
    """
    Build intelligent prompt for Stable Audio from vocal characteristics.
    
    Args:
        genre: Musical genre
        bpm: Tempo in beats per minute
        key: Musical key
        mood: Emotional mood
        density_hints: Optional breath/density information
        vocal_dna: Optional full vocal analysis
    
    Returns:
        Optimized prompt string for Stable Audio
    """
    # Core musical elements
    prompt_parts = [
        f"{mood} {genre} instrumental",
        f"{bpm} BPM",
        f"{key}",
    ]
    
    # Mood-based instrumentation
    mood_instruments = {
        "aggressive": "heavy bass, distorted synths, punchy drums, dark atmosphere",
        "introspective": "ambient pads, soft piano, subtle percussion, atmospheric textures",
        "playful": "bright synths, bouncy bass, melodic elements, upbeat energy",
        "melancholic": "strings, reverb piano, emotional depth, atmospheric layers",
        "energetic": "driving bass, layered synths, dynamic drums, uplifting vibes",
        "chill": "lo-fi beats, warm pads, smooth bass, relaxed atmosphere"
    }
    
    instruments = mood_instruments.get(mood, "layered instrumentation, melodic elements")
    prompt_parts.append(instruments)
    
    # Breath-aware density hints
    if density_hints:
        breath_count = density_hints.get('breath_gap_count', 0)
        avg_presence = density_hints.get('avg_presence', 0.5)
        
        if breath_count > 5:
            # Lots of silence = space for fills
            prompt_parts.append("sparse arrangement with space for vocals, breathing instrumentation")
        else:
            # Dense vocal = full backing
            prompt_parts.append("full rich arrangement, dense production")
    
    # Vocal characteristics (if provided)
    if vocal_dna:
        rms = vocal_dna.get('rms', 0.1)
        if rms < 0.08:
            prompt_parts.append("subtle gentle backing, delicate dynamics")
        elif rms > 0.15:
            prompt_parts.append("powerful dynamic backing, strong presence")
    
    # Audio quality descriptors (important for Stable Audio)
    prompt_parts.append("high quality professional production, cohesive arrangement")
    
    return ", ".join(prompt_parts)


def generate_beat_replicate(
    genre: str,
    bpm: int,
    key: str,
    mood: str,
    duration: int = 30,
    density_hints: dict = None,
    vocal_dna: dict = None
) -> str:
    """
    Generate professional instrumental using Stable Audio on Replicate.
    
    Stable Audio produces higher quality, more structured compositions
    than MusicGen while using the same simple Replicate API.
    
    Args:
        genre: Musical genre (e.g., "Trap", "Alt-R&B", "Drill")
        bpm: Tempo in beats per minute
        key: Musical key (e.g., "C minor", "D major")
        mood: Emotional mood (e.g., "aggressive", "introspective")
        duration: Length in seconds (max 47s for open model)
        density_hints: Optional dict with 'breath_gap_count' and 'avg_presence'
        vocal_dna: Optional full vocal analysis for better prompts
    
    Returns:
        Path to generated WAV file
    """
    print(f"🎵 Generating {genre} instrumentation via Stable Audio...")
    print(f"  └─ BPM: {bpm}, Key: {key}, Mood: {mood}")
    
    # Build intelligent prompt from vocal DNA
    prompt = build_stable_audio_prompt(
        genre=genre,
        bpm=bpm,
        key=key,
        mood=mood,
        density_hints=density_hints,
        vocal_dna=vocal_dna
    )
    
    if density_hints:
        gap_count = density_hints.get('breath_gap_count', 0)
        print(f"  └─ Breathing Arrangement: {gap_count} breath gaps - optimizing instrumentation")
    
    print(f"  └─ Prompt: {prompt[:80]}...")
    print(f"  └─ Calling Stable Audio via Replicate...")
    
    try:
        # Use Stable Audio 2.5 - Professional quality with audio-to-audio support
        output = replicate.run(
            "stability-ai/stable-audio-2.5",  # Correct model path
            input={
                "prompt": prompt,
                "seconds_total": min(duration, 180),  # Max 3 minutes for v2.5
                "cfg_scale": 7.0,  # Prompt adherence (1-15, default 7)
                "steps": 8,  # Max steps for v2.5 (different from v2.0)
                "seed": -1  # Random seed for variety
            }
        )


        
        # Download the generated audio
        # Stable Audio returns a URL to the audio file
        audio_url = output
        print(f"  └─ Downloading generated audio...")
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()
        
        output_path = "generated_beat_stable.wav"
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Instrumentation generated: {output_path}")
        return output_path
    
    except Exception as e:
        raise Exception(f"Stable Audio generation failed: {str(e)}")
