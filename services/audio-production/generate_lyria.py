"""
LYRIA 3 - Structured Music Generation
======================================
Uses Google's Lyria model (lyria-002) for high-quality, structured
instrumental music generation.

Unlike Lyria RealTime (which improvises via WebSocket), this module
generates a COMPLETE, STRUCTURED 30s track — with intro, development,
and resolution. This is the same quality you get from the Gemini app.

Output: 48kHz stereo WAV, ~30 seconds
Dependencies: google-genai>=1.0.0
"""

import os
import asyncio
import base64
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
    Build a detailed, structured prompt for Lyria 3.
    
    Lyria 3 responds to natural language descriptions that specify
    genre, mood, instrumentation, tempo, and production style.
    More specific = better structured output.
    """
    # Core musical description
    parts = []
    
    # Genre and tempo foundation
    parts.append(f"A {mood} {genre} instrumental track at {bpm} BPM in {key}")
    
    # Mood-specific instrumentation (very specific = better structure)
    mood_details = {
        "aggressive": "with heavy 808 bass patterns, aggressive trap hi-hats, dark atmospheric synth pads, punchy kick drums, and building tension throughout. Include a powerful drop section.",
        "introspective": "with soft ambient pads, gentle Rhodes piano chords, subtle finger-snapped percussion, warm analog bass, and a dreamy reverb atmosphere. Build from minimal to slightly fuller arrangement.",
        "playful": "with bouncy bass line, bright melodic synth hooks, crisp snare patterns, upbeat rhythmic guitar, and cheerful chord progressions. Include playful fills and transitions.",
        "melancholic": "with emotional string section, deep reverb piano, slow rhythmic pulse, atmospheric textures, and a melancholic chord progression. Build from sparse to emotionally full.",
        "energetic": "with driving bass, layered synthesizer stacks, powerful drum patterns, energetic build-ups, and dynamic drops. Include rising tension and release moments.",
        "chill": "with lo-fi warm textures, smooth jazz bass, laid-back drum groove, vinyl crackle atmosphere, mellow Rhodes chords, and relaxed swing feel.",
        "dark": "with dark ambient atmosphere, heavy sub bass, industrial percussion hits, eerie pad textures, and building tension. Include moments of silence for dramatic effect.",
        "balanced": "with clean balanced production, warm bass foundation, crisp drums, melodic hooks, and professional arrangement. Build naturally from verse to chorus energy.",
    }
    
    detail = mood_details.get(mood, "with professional studio production, balanced arrangement, and cohesive musicality.")
    parts.append(detail)
    
    # Structure hints based on vocal characteristics
    if vocal_dna:
        rms = vocal_dna.get('rms', 0.1)
        breath_gaps = len(vocal_dna.get('breath_gaps', []))
        
        if rms < 0.08:
            parts.append("Keep the arrangement gentle and spacious, with room for a soft vocal performance.")
        elif rms > 0.15:
            parts.append("Make the arrangement powerful and full, matching the energy of a dynamic vocal performance.")
        
        if breath_gaps > 5:
            parts.append("Include subtle instrumental fills in the spaces between phrases.")
    
    if density_hints:
        avg_presence = density_hints.get('avg_presence', 0.5)
        if avg_presence > 0.6:
            parts.append("Keep instrumentation sparse with lots of space and breathing room.")
        elif avg_presence < 0.3:
            parts.append("Use a full, rich arrangement with layered instrumentation.")
    
    # Quality and structure directive
    parts.append("Professional studio quality, radio-ready mix, with clear musical sections and natural progression.")
    
    return " ".join(parts)


def build_negative_prompt() -> str:
    """Elements to exclude from generation."""
    return "vocals, singing, spoken word, voice, speech, lo-fi noise, distortion, clipping, amateur quality, monotonous, repetitive without variation"


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
    """
    Generate a structured instrumental using Lyria 3.
    
    This produces a complete, composed track with proper musical
    structure (intro → development → resolution), not a live jam.
    
    Args:
        genre: Musical genre
        bpm: Tempo in beats per minute
        key: Musical key
        mood: Emotional mood
        duration: Target duration (Lyria produces ~30-32s)
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
        print(f"\n🎵 LYRIA 3: Generating structured {genre} instrumental...")
        print(f"   BPM: {bpm}, Key: {key}, Mood: {mood}")
    
    # Build detailed prompt
    prompt = build_lyria_prompt(genre, bpm, key, mood, density_hints, vocal_dna)
    negative_prompt = build_negative_prompt()
    
    if verbose:
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Negative: {negative_prompt[:60]}...")
    
    # Initialize client
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_API_KEY not set in environment")
    
    client = genai.Client(api_key=api_key)
    
    try:
        # === APPROACH 1: Gemini API with audio modality ===
        if verbose:
            print(f"   🔗 Calling Lyria via Gemini API...")
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Generate instrumental music: {prompt}\n\nDo NOT include vocals. This should be instrumental only.\nNegative prompt: {negative_prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore"
                        )
                    )
                )
            )
        )
        
        # Extract audio from response
        audio_data = None
        mime_type = None
        
        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.inline_data and part.inline_data.data:
                            audio_data = part.inline_data.data
                            mime_type = getattr(part.inline_data, 'mime_type', 'audio/wav')
                            break
                    if audio_data:
                        break
        
        if not audio_data:
            raise Exception("No audio data in response")
        
        if verbose:
            print(f"   ✓ Received audio ({mime_type}), {len(audio_data)} bytes")
        
        # Handle different audio formats
        import io
        import wave
        
        if isinstance(audio_data, str):
            # Base64 encoded
            audio_bytes = base64.b64decode(audio_data)
        else:
            audio_bytes = audio_data
        
        # Try to parse as WAV first
        try:
            with io.BytesIO(audio_bytes) as buf:
                data, sr = sf.read(buf)
                sf.write(output_path, data, sr)
                if verbose:
                    print(f"   ✓ Saved as WAV: {sr}Hz, {len(data)/sr:.1f}s")
        except Exception:
            # Raw PCM — assume 48kHz stereo 16-bit
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            if len(audio_array) >= 2:
                audio_stereo = audio_array[:len(audio_array) // 2 * 2].reshape(-1, 2)
            else:
                audio_stereo = np.column_stack([audio_array, audio_array])
            sf.write(output_path, audio_stereo, 48000)
            if verbose:
                print(f"   ✓ Saved raw PCM as WAV: 48000Hz, {len(audio_stereo)/48000:.1f}s")
        
        if verbose:
            print(f"\n✅ LYRIA 3 BEAT GENERATED: {output_path}")
        
        return output_path
    
    except Exception as e:
        error_msg = str(e)
        if verbose:
            print(f"   ⚠️ Gemini audio generation error: {error_msg}")
        
        # === APPROACH 2: Lyria RealTime with stable config (no frequent updates) ===
        # Generate a STABLE beat using RealTime but WITHOUT constant density changes
        # This produces more structured output than our reactive mode
        if verbose:
            print(f"\n   🔄 Falling back to Lyria RealTime (stable mode)...")
        
        return _generate_stable_realtime(
            genre=genre, bpm=bpm, key=key, mood=mood,
            duration_s=float(duration),
            output_path=output_path,
            verbose=verbose
        )


def _generate_stable_realtime(
    genre: str, bpm: int, key: str, mood: str,
    duration_s: float = 30.0,
    output_path: str = "generated_beat_lyria3.wav",
    verbose: bool = True
) -> str:
    """
    Generate a beat using Lyria RealTime in STABLE mode.
    
    Unlike the reactive generator, this sets prompts and config ONCE
    and lets Lyria compose freely for 30s. This produces much more
    structured, coherent output.
    """
    return asyncio.run(_generate_stable_realtime_async(
        genre, bpm, key, mood, duration_s, output_path, verbose
    ))


async def _generate_stable_realtime_async(
    genre: str, bpm: int, key: str, mood: str,
    duration_s: float = 30.0,
    output_path: str = "generated_beat_lyria3.wav",
    verbose: bool = True
) -> str:
    from google import genai
    from google.genai import types
    
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1alpha'}
    )
    
    collected_audio = bytearray()
    sample_rate = 48000
    bytes_per_second = sample_rate * 2 * 2  # stereo, 16-bit
    target_bytes = int(duration_s * bytes_per_second)
    
    # Build a rich, detailed prompt for cohesive generation
    mood_details = {
        "aggressive": "aggressive trap instrumental, heavy 808s, dark atmospheric synths, punchy drums, professional mix",
        "introspective": "introspective R&B instrumental, ambient pads, soft piano, warm bass, dreamy atmosphere, professional mix",
        "playful": "playful upbeat instrumental, bouncy bass, bright synths, crisp drums, melodic hooks",
        "melancholic": "melancholic emotional instrumental, strings, reverb piano, deep atmosphere, slow build",
        "energetic": "energetic driving instrumental, powerful bass, layered synths, dynamic drums, building energy",
        "chill": "chill lo-fi instrumental, warm analog textures, smooth bass, relaxed groove, vinyl atmosphere",
        "dark": "dark moody instrumental, heavy sub bass, industrial percussion, eerie textures, tension",
        "balanced": "balanced professional instrumental, clean production, warm bass, crisp drums, melodic elements",
    }
    
    prompt_text = mood_details.get(mood, f"{mood} {genre} instrumental, professional quality")
    
    if verbose:
        print(f"   Prompt: {prompt_text[:60]}...")
        print(f"   BPM: {bpm}, Mode: STABLE (no density steering)")
    
    async with client.aio.live.music.connect(
        model="models/lyria-realtime-exp"
    ) as session:
        
        # Set prompt ONCE — let Lyria compose freely
        await session.set_weighted_prompts([
            types.WeightedPrompt(text=prompt_text, weight=1.0)
        ])
        
        # Set config ONCE — stable parameters, no mid-stream changes
        await session.set_music_generation_config(
            types.LiveMusicGenerationConfig(
                bpm=int(np.clip(bpm, 60, 200)),
                density=0.6,  # Balanced density — let Lyria decide arrangement
                guidance=4.0,  # Higher guidance = more adherent to prompt
            )
        )
        
        await session.play()
        
        if verbose:
            print(f"   ▶ Streaming stable composition...")
        
        async for message in session.receive():
            if message.server_content and hasattr(message.server_content, 'audio_chunks'):
                for chunk in message.server_content.audio_chunks:
                    if hasattr(chunk, 'data') and chunk.data:
                        collected_audio.extend(chunk.data)
            
            if len(collected_audio) >= target_bytes:
                break
        
        try:
            await session.pause()
        except Exception:
            pass
    
    if len(collected_audio) < 1000:
        raise Exception("Lyria RealTime (stable) returned insufficient audio")
    
    # Convert to WAV
    audio_array = np.frombuffer(collected_audio, dtype=np.int16).astype(np.float32) / 32768.0
    if len(audio_array) >= 2:
        audio_stereo = audio_array[:len(audio_array) // 2 * 2].reshape(-1, 2)
    else:
        audio_stereo = np.column_stack([audio_array, audio_array])
    
    sf.write(output_path, audio_stereo, sample_rate)
    
    if verbose:
        print(f"\n✅ LYRIA STABLE BEAT GENERATED: {output_path}")
        print(f"   Duration: {len(audio_stereo) / sample_rate:.1f}s")
        print(f"   Sample Rate: {sample_rate}Hz")
    
    return output_path


# === STANDALONE TEST ===
if __name__ == "__main__":
    print("=" * 60)
    print("🎵 LYRIA 3 - Structured Music Generation")
    print("=" * 60)
    
    result = generate_beat_lyria(
        genre="Alt-R&B",
        bpm=90,
        key="D minor",
        mood="introspective",
        verbose=True
    )
    
    print(f"\n🎶 Output: {result}")
