"""
LYRIA 3 - High-Quality Text-to-Music Generation
=================================================
Fallback/simple beat generation using Lyria 3 via the Gemini API.

Unlike Lyria RealTime (which streams with live control), this module
generates a complete 30s track from a text prompt. It's used as:
1. A fast fallback when RealTime isn't available
2. Phase 1 quick swap (replacing Stable Audio)

Output: 48kHz stereo WAV, ~30 seconds

Dependencies: google-genai>=1.0.0
"""

import os
import asyncio
import numpy as np
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()


def build_lyria_prompt(
    genre: str,
    bpm: int,
    key: str,
    mood: str,
    density_hints: dict = None,
    vocal_dna: dict = None
) -> str:
    """
    Build an optimized text prompt for Lyria 3 music generation.
    
    Lyria responds best to descriptive, natural-language style prompts
    with concrete musical terms.
    """
    prompt_parts = [
        f"{mood} {genre} instrumental",
        f"{bpm} BPM",
        f"{key}",
    ]
    
    # Mood-based instrumentation
    mood_instruments = {
        "aggressive": "heavy 808s, distorted synths, punchy trap drums, dark atmosphere",
        "introspective": "ambient pads, soft piano, subtle percussion, atmospheric textures, reverb",
        "playful": "bright synths, bouncy bass, melodic hooks, upbeat energy",
        "melancholic": "emotional strings, reverb piano, deep atmosphere, minor key",
        "energetic": "driving bass, layered synths, dynamic drums, uplifting progression",
        "chill": "lo-fi beats, warm analog pads, smooth bass, relaxed groove",
        "dark": "dark ambient, heavy sub bass, industrial percussion, tension",
        "balanced": "clean production, balanced mix, professional arrangement",
    }
    
    instruments = mood_instruments.get(mood, "layered instrumentation, melodic elements")
    prompt_parts.append(instruments)
    
    # Breath-aware density hints
    if density_hints:
        breath_count = density_hints.get('breath_gap_count', 0)
        if breath_count > 5:
            prompt_parts.append("sparse arrangement with space for vocals, breathing instrumentation")
        else:
            prompt_parts.append("full rich arrangement, dense production")
    
    # Vocal RMS-based intensity  
    if vocal_dna:
        rms = vocal_dna.get('rms', 0.1)
        if rms < 0.08:
            prompt_parts.append("subtle gentle backing, delicate dynamics")
        elif rms > 0.15:
            prompt_parts.append("powerful dynamic backing, strong presence")
    
    prompt_parts.append("high quality professional studio production, cohesive, radio-ready")
    
    return ", ".join(prompt_parts)


def build_negative_prompt(genre: str) -> str:
    """Build a negative prompt to exclude unwanted elements."""
    exclusions = [
        "vocals", "singing", "spoken word",  # We want instrumental only
        "noise", "distortion", "clipping",
        "low quality", "amateur",
    ]
    return ", ".join(exclusions)


async def generate_beat_lyria_async(
    genre: str = "Alt-R&B",
    bpm: int = 90,
    key: str = "D minor",
    mood: str = "introspective",
    duration: int = 30,
    density_hints: dict = None,
    vocal_dna: dict = None,
    output_path: str = "generated_beat_lyria3.wav",
    verbose: bool = True
) -> str:
    """
    Generate professional instrumental using Lyria 3 via Gemini API.
    
    This is a one-shot generation (not reactive/streaming like RealTime).
    Used as fallback when RealTime is unavailable or for quick generation.
    
    Args:
        genre: Musical genre
        bpm: Tempo in beats per minute
        key: Musical key
        mood: Emotional mood
        duration: Target duration in seconds (max 30s for Lyria)
        density_hints: Optional breath/density info
        vocal_dna: Optional vocal analysis
        output_path: Where to save output
        verbose: Print progress
        
    Returns:
        Path to generated WAV file
    """
    from google import genai
    from google.genai import types
    
    if verbose:
        print(f"\n🎵 LYRIA 3: Generating {genre} instrumental...")
        print(f"   BPM: {bpm}, Key: {key}, Mood: {mood}")
    
    # Build prompt
    prompt = build_lyria_prompt(genre, bpm, key, mood, density_hints, vocal_dna)
    negative_prompt = build_negative_prompt(genre)
    
    if verbose:
        print(f"   Prompt: {prompt[:80]}...")
    
    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_API_KEY not set in environment")
    
    client = genai.Client(api_key=api_key)
    
    try:
        # Generate using Lyria model
        # Try lyria-002 (Vertex AI style) for text-to-music
        response = await client.aio.models.generate_content(
            model="lyria-002",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=None,  # We want music, not speech
            )
        )
        
        # Extract audio data from response
        audio_data = None
        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.inline_data and part.inline_data.data:
                            audio_data = part.inline_data.data
                            break
        
        if not audio_data:
            raise Exception("No audio data in Lyria 3 response")
        
        # Save audio
        # Lyria outputs 48kHz stereo
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        if len(audio_array) >= 2:
            audio_stereo = audio_array[:len(audio_array) // 2 * 2].reshape(-1, 2)
        else:
            audio_stereo = np.column_stack([audio_array, audio_array])
        
        sf.write(output_path, audio_stereo, 48000)
        
        if verbose:
            print(f"\n✅ LYRIA 3 BEAT GENERATED: {output_path}")
            print(f"   Duration: {len(audio_stereo) / 48000:.1f}s")
        
        return output_path
    
    except Exception as e:
        raise Exception(f"Lyria 3 generation failed: {str(e)}")


def generate_beat_lyria(
    genre: str = "Alt-R&B",
    bpm: int = 90,
    key: str = "D minor",
    mood: str = "introspective",
    duration: int = 30,
    density_hints: dict = None,
    vocal_dna: dict = None,
    output_path: str = "generated_beat_lyria3.wav",
    verbose: bool = True
) -> str:
    """Synchronous wrapper for Lyria 3 generation."""
    return asyncio.run(generate_beat_lyria_async(
        genre=genre, bpm=bpm, key=key, mood=mood,
        duration=duration, density_hints=density_hints,
        vocal_dna=vocal_dna, output_path=output_path,
        verbose=verbose
    ))


# === STANDALONE TEST ===
if __name__ == "__main__":
    print("=" * 60)
    print("🎵 LYRIA 3 - Text-to-Music Generation")
    print("=" * 60)
    
    result = generate_beat_lyria(
        genre="Alt-R&B",
        bpm=90,
        key="D minor",
        mood="introspective",
        verbose=True
    )
    
    print(f"\n🎶 Output: {result}")
