"""
LYRIA REALTIME - Vocal-Reactive Beat Generation
================================================
Uses Google's Lyria RealTime API (WebSocket) to generate instrumental
music that BREATHES with the vocal performance.

Key Innovation:
- The vocal's energy envelope drives Lyria's 'density' parameter in real-time
- When singer is loud → density drops → instrumentation thins
- When singer breathes → density rises → fills appear
- BPM and Scale are locked to match the vocal exactly

This replaces the old workflow of:
  Generate blind beat → Demucs separate → Post-hoc sidechain
With:
  Analyze vocal → Stream reactive beat from Lyria

Dependencies: google-genai>=1.0.0
"""

import os
import asyncio
import numpy as np
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional, List

load_dotenv()


# === SCALE MAPPING ===
# Maps musical key strings to Lyria Scale identifiers
SCALE_MAP = {
    "C major": "C_MAJOR", "C minor": "C_MINOR",
    "C# major": "C_SHARP_MAJOR", "C# minor": "C_SHARP_MINOR",
    "D major": "D_MAJOR", "D minor": "D_MINOR",
    "D# major": "D_SHARP_MAJOR", "D# minor": "D_SHARP_MINOR",
    "E major": "E_MAJOR", "E minor": "E_MINOR",
    "F major": "F_MAJOR", "F minor": "F_MINOR",
    "F# major": "F_SHARP_MAJOR", "F# minor": "F_SHARP_MINOR",
    "G major": "G_MAJOR", "G minor": "G_MINOR",
    "G# major": "G_SHARP_MAJOR", "G# minor": "G_SHARP_MINOR",
    "A major": "A_MAJOR", "A minor": "A_MINOR",
    "A# major": "A_SHARP_MAJOR", "A# minor": "A_SHARP_MINOR",
    "B major": "B_MAJOR", "B minor": "B_MINOR",
}


def build_genre_prompts(genre: str, mood: str) -> List[dict]:
    """
    Build weighted prompts that guide Lyria's musical style.
    
    Returns a list of prompt dicts for different musical aspects,
    each with its own weight for blending.
    """
    # Primary genre prompt (strongest influence)
    prompts = [
        {"text": f"{mood} {genre} instrumental, professional mix, high quality", "weight": 1.0}
    ]
    
    # Mood-specific secondary prompts for nuance
    mood_prompts = {
        "aggressive": {"text": "heavy bass, dark synths, punchy 808s, trap energy", "weight": 0.6},
        "introspective": {"text": "ambient pads, soft keys, atmospheric, dreamy", "weight": 0.6},
        "playful": {"text": "bright melodies, bouncy bass, upbeat groove", "weight": 0.6},
        "melancholic": {"text": "emotional strings, reverb piano, deep atmosphere", "weight": 0.6},
        "energetic": {"text": "driving rhythm, layered synths, powerful drops", "weight": 0.6},
        "chill": {"text": "lo-fi textures, warm analog, smooth jazz bass", "weight": 0.6},
        "dark": {"text": "dark atmosphere, minor key, heavy sub bass", "weight": 0.6},
        "balanced": {"text": "balanced mix, clean production, radio ready", "weight": 0.5},
    }
    
    if mood in mood_prompts:
        prompts.append(mood_prompts[mood])
    
    return prompts


def compute_density_timeline(vocal_dna: Dict, target_duration_s: float = 30.0) -> List[float]:
    """
    Convert vocal DNA into a density timeline for Lyria RealTime.
    
    Logic:
    - Where vocalist is LOUD → density LOW (space for voice)
    - Where vocalist is SILENT → density HIGH (instrumental fills)
    - Smooth transitions to avoid jarring changes
    
    Returns:
        List of density values (0.1 to 0.9) sampled at ~2Hz
    """
    density_env = vocal_dna.get('density_envelope', [])
    
    if not density_env:
        # Fallback: constant medium density
        num_points = int(target_duration_s * 2)  # 2 updates per second
        return [0.5] * num_points
    
    # Resample density envelope to ~2Hz (one update every 500ms)
    num_points = int(target_duration_s * 2)
    x_original = np.linspace(0, 1, len(density_env))
    x_target = np.linspace(0, 1, num_points)
    resampled = np.interp(x_target, x_original, density_env)
    
    # Clip to safe range and apply smoothing
    from scipy.ndimage import uniform_filter1d
    smoothed = uniform_filter1d(resampled, size=3)
    clipped = np.clip(smoothed, 0.1, 0.9)
    
    return clipped.tolist()


def compute_section_prompts(vocal_dna: Dict, target_duration_s: float = 30.0) -> List[dict]:
    """
    Generate timed prompt changes based on phrase markers.
    
    Detects verse-like (quiet) vs chorus-like (loud) sections
    and prepares prompt transitions.
    
    Returns:
        List of {"time_s": float, "prompt": str, "weight": float}
    """
    phrase_markers = vocal_dna.get('phraseMarkers', [])
    energy_env = vocal_dna.get('energyEnvelope', [])
    
    if not phrase_markers or not energy_env:
        return []
    
    # Calculate average energy per phrase
    total_duration = phrase_markers[-1]['end'] if phrase_markers else target_duration_s
    sections = []
    
    for marker in phrase_markers:
        # Map phrase time to energy envelope index
        start_idx = int((marker['start'] / total_duration) * len(energy_env))
        end_idx = int((marker['end'] / total_duration) * len(energy_env))
        start_idx = max(0, min(start_idx, len(energy_env) - 1))
        end_idx = max(start_idx + 1, min(end_idx, len(energy_env)))
        
        phrase_energy = np.mean(energy_env[start_idx:end_idx])
        
        if phrase_energy > 0.6:
            sections.append({
                "time_s": marker['start'],
                "prompt": "full energy, powerful backing, anthemic",
                "weight": 0.8
            })
        elif phrase_energy < 0.3:
            sections.append({
                "time_s": marker['start'],
                "prompt": "minimal, intimate, sparse, space for vocals",
                "weight": 0.8
            })
    
    return sections


async def generate_reactive_beat(
    vocal_path: str,
    genre: str = "Alt-R&B",
    bpm: int = 90,
    key: str = "D minor",
    mood: str = "introspective",
    duration_s: float = 30.0,
    vocal_dna: Optional[Dict] = None,
    output_path: str = "generated_beat_lyria.wav",
    verbose: bool = True
) -> str:
    """
    Generate a beat that BREATHES with the vocal using Lyria RealTime.
    
    The density parameter is driven by the vocal's inverse energy envelope,
    creating natural sparse/dense transitions aligned to the performance.
    
    Args:
        vocal_path: Path to vocal audio file
        genre: Musical genre (e.g., "Trap", "Alt-R&B", "Drill")
        bpm: Tempo locked to vocal's BPM
        key: Musical key (e.g., "D minor", "C major")
        mood: Emotional mood for prompt styling
        duration_s: Target duration in seconds
        vocal_dna: Pre-extracted vocal DNA (if None, will extract)
        output_path: Where to save the generated beat
        verbose: Print progress
        
    Returns:
        Path to generated WAV file
    """
    from google import genai
    from google.genai import types
    
    if verbose:
        print(f"\n🎵 LYRIA REALTIME: Generating vocal-reactive beat...")
        print(f"   Genre: {genre}")
        print(f"   BPM: {bpm} (locked to vocal)")
        print(f"   Key: {key}")
        print(f"   Mood: {mood}")
    
    # 1. Extract vocal DNA if not provided
    if vocal_dna is None:
        from vocal_intel import extract_vocal_dna
        vocal_dna = extract_vocal_dna(vocal_path, verbose=verbose)
    
    # 2. Build density timeline from vocal DNA
    density_timeline = compute_density_timeline(vocal_dna, duration_s)
    
    if verbose:
        avg_density = np.mean(density_timeline)
        print(f"   Density Range: {min(density_timeline):.2f} - {max(density_timeline):.2f}")
        print(f"   Avg Density: {avg_density:.2f}")
        print(f"   → {'Sparse arrangement (vocal-heavy)' if avg_density < 0.4 else 'Full arrangement (vocal-light)' if avg_density > 0.6 else 'Balanced arrangement'}")
    
    # 3. Build section-aware prompts
    section_prompts = compute_section_prompts(vocal_dna, duration_s)
    
    # 4. Map key string to Lyria Scale
    scale_key = SCALE_MAP.get(key, "D_MINOR")
    
    # 5. Build genre prompts
    genre_prompts = build_genre_prompts(genre, mood)
    
    # 6. Connect to Lyria RealTime
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_API_KEY not set in environment")
    
    client = genai.Client(api_key=api_key)
    collected_audio = bytearray()
    
    if verbose:
        print(f"\n   🔗 Connecting to Lyria RealTime (WebSocket)...")
    
    try:
        async with client.aio.live.music.connect(
            model="lyria-realtime-exp"
        ) as session:
            
            # Set initial musical prompt
            weighted_prompts = [
                types.WeightedPrompt(text=p["text"], weight=p["weight"])
                for p in genre_prompts
            ]
            await session.set_weighted_prompts(weighted_prompts)
            
            if verbose:
                print(f"   ✓ Prompts set: {genre_prompts[0]['text'][:60]}...")
            
            # Set initial generation config
            config = types.MusicGenerationConfig(
                bpm=int(np.clip(bpm, 60, 200)),
                density=float(density_timeline[0]) if density_timeline else 0.5,
                guidance=3.5,
            )
            
            # Try to set scale if the types support it
            try:
                config.scale = getattr(types.Scale, scale_key, None)
            except (AttributeError, TypeError):
                pass  # Scale enum might not be available in all SDK versions
            
            await session.set_music_generation_config(config)
            
            if verbose:
                print(f"   ✓ Config: BPM={bpm}, Scale={scale_key}, Density={density_timeline[0]:.2f}")
            
            # Start generation
            await session.play()
            
            if verbose:
                print(f"   ▶ Streaming audio...")
            
            # Receive audio while dynamically steering density
            sample_rate = 48000  # Lyria outputs 48kHz
            bytes_per_second = sample_rate * 2 * 2  # stereo, 16-bit
            target_bytes = int(duration_s * bytes_per_second)
            density_update_interval = 0.5  # Update density every 500ms
            density_idx = 0
            section_idx = 0
            
            async for message in session.receive():
                if message.server_content and message.server_content.model_turn:
                    for part in message.server_content.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            collected_audio.extend(part.inline_data.data)
                
                # Calculate current time position
                current_time_s = len(collected_audio) / bytes_per_second
                
                # Update density based on vocal energy envelope
                new_density_idx = min(
                    int(current_time_s / density_update_interval),
                    len(density_timeline) - 1
                )
                
                if new_density_idx > density_idx and new_density_idx < len(density_timeline):
                    density_idx = new_density_idx
                    new_density = float(density_timeline[density_idx])
                    
                    try:
                        await session.set_music_generation_config(
                            types.MusicGenerationConfig(
                                density=new_density
                            )
                        )
                    except Exception:
                        pass  # Ignore transient config update errors
                
                # Update section prompts if we've reached a new section
                if section_idx < len(section_prompts):
                    section = section_prompts[section_idx]
                    if current_time_s >= section['time_s']:
                        try:
                            await session.set_weighted_prompts([
                                types.WeightedPrompt(
                                    text=section['prompt'],
                                    weight=section['weight']
                                )
                            ] + weighted_prompts)  # Keep base prompt
                            if verbose:
                                print(f"   🎭 Section prompt @ {current_time_s:.1f}s: {section['prompt'][:40]}...")
                        except Exception:
                            pass
                        section_idx += 1
                
                # Check if we have enough audio
                if len(collected_audio) >= target_bytes:
                    break
            
            # Stop generation
            try:
                await session.pause()
            except Exception:
                pass
        
        if verbose:
            print(f"   ✓ Received {len(collected_audio)} bytes ({len(collected_audio)/bytes_per_second:.1f}s)")
    
    except Exception as e:
        raise Exception(f"Lyria RealTime generation failed: {str(e)}")
    
    # 7. Convert raw bytes to WAV
    if len(collected_audio) < 1000:
        raise Exception("Lyria RealTime returned insufficient audio data")
    
    audio_array = np.frombuffer(collected_audio, dtype=np.int16).astype(np.float32) / 32768.0
    
    # Reshape to stereo (Lyria outputs interleaved stereo)
    if len(audio_array) >= 2:
        audio_stereo = audio_array[:len(audio_array) // 2 * 2].reshape(-1, 2)
    else:
        audio_stereo = np.column_stack([audio_array, audio_array])
    
    sf.write(output_path, audio_stereo, sample_rate)
    
    if verbose:
        print(f"\n✅ LYRIA REALTIME BEAT GENERATED: {output_path}")
        print(f"   Duration: {len(audio_stereo) / sample_rate:.1f}s")
        print(f"   Sample Rate: {sample_rate}Hz")
        print(f"   Density Updates: {density_idx} reactive adjustments")
    
    return output_path


def generate_reactive_beat_sync(
    vocal_path: str,
    genre: str = "Alt-R&B",
    bpm: int = 90,
    key: str = "D minor",
    mood: str = "introspective",
    duration_s: float = 30.0,
    vocal_dna: Optional[Dict] = None,
    output_path: str = "generated_beat_lyria.wav",
    verbose: bool = True
) -> str:
    """
    Synchronous wrapper for generate_reactive_beat.
    Use this from non-async contexts (e.g., FastAPI background tasks).
    """
    return asyncio.run(generate_reactive_beat(
        vocal_path=vocal_path,
        genre=genre,
        bpm=bpm,
        key=key,
        mood=mood,
        duration_s=duration_s,
        vocal_dna=vocal_dna,
        output_path=output_path,
        verbose=verbose
    ))


# === STANDALONE TEST ===
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        vocal_file = sys.argv[1]
    else:
        vocal_file = "test_vocal.wav"
    
    if not os.path.exists(vocal_file):
        print(f"❌ Vocal file not found: {vocal_file}")
        print("Usage: python generate_lyria_realtime.py <vocal_file>")
        sys.exit(1)
    
    print("=" * 60)
    print("🎙️ LYRIA REALTIME - Vocal-Reactive Beat Generation")
    print("=" * 60)
    
    result = generate_reactive_beat_sync(
        vocal_path=vocal_file,
        genre="Alt-R&B",
        mood="introspective",
        verbose=True
    )
    
    print(f"\n🎶 Output: {result}")
