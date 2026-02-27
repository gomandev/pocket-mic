"""
Vocal-Aware Stem-Based Mixing
Intelligently mixes separated stems with vocal based on DNA characteristics
"""
import librosa
import numpy as np
from pathlib import Path


def mix_vocal_and_stems(
    vocal_path: str,
    stems: dict,  # {'drums': path, 'bass': path, 'other': path}
    vocal_dna: dict,
    verbose: bool = False
) -> str:
    """
    Intelligent multi-stem mixing with vocal awareness.
    
    Each stem is processed based on vocal characteristics to:
    - Eliminate frequency clashes
    - Preserve vocal clarity
    - Create dynamic breathing arrangement
    
    Args:
        vocal_path: Path to vocal audio
        stems: Dict of stem paths {'drums': ..., 'bass': ..., 'other': ...}
        vocal_dna: Vocal characteristics from vocal_intel
        verbose: Print mixing decisions
    
    Returns:
        Path to final mixed audio
    """
    if verbose:
        print("\n🎚️ STEM-BASED VOCAL-AWARE MIXING...")
    
    # Load vocal
    vocal, sr = librosa.load(vocal_path, sr=None, mono=False)
    if vocal.ndim == 1:
        vocal = np.stack([vocal, vocal])  # Convert mono to stereo
    
    # Load stems
    stems_audio = {}
    for stem_name, stem_path in stems.items():
        audio, _ = librosa.load(stem_path, sr=sr, mono=False)
        if audio.ndim == 1:
            audio = np.stack([audio, audio])
        stems_audio[stem_name] = audio
        
        if verbose:
            print(f"   ✓ Loaded {stem_name} stem")
    
    # Get vocal characteristics
    vocal_center = vocal_dna.get('spectral_center', 1500)
    vocal_rms = vocal_dna.get('rms', 0.1)
    breath_gaps = len(vocal_dna.get('breath_gaps', []))
    
    if verbose:
        print(f"\n   Vocal DNA Analysis:")
        print(f"   • Spectral Center: {vocal_center:.0f}Hz")
        print(f"   • RMS Level: {vocal_rms:.3f}")
        print(f"   • Breath Gaps: {breath_gaps}")
    
    # INTELLIGENT MIX LEVELS based on vocal characteristics
    
    # Base levels
    levels = {
        'vocal': 1.0,  # Vocal is always primary
        'drums': 0.65,
        'bass': 0.75,
        'other': 0.55
    }
    
    # Adjust based on vocal energy
    if vocal_rms > 0.15:
        # Powerful vocal = quieter backing
        if verbose:
            print(f"\n   Mixing Strategy: POWERFUL VOCAL")
            print(f"   └─ Reducing instrument levels for clarity")
        levels['drums'] *= 0.85
        levels['bass'] *= 0.9
        levels['other'] *= 0.75
    elif vocal_rms < 0.08:
        # Soft vocal = more supporting instrumentation
        if verbose:
            print(f"\n   Mixing Strategy: DELICATE VOCAL")
            print(f"   └─ Boosting instruments for support")
        levels['drums'] *= 1.1
        levels['bass'] *= 1.15
        levels['other'] *= 1.2
    else:
        if verbose:
            print(f"\n   Mixing Strategy: BALANCED")
    
    # Adjust for breath gaps (breathing arrangement)
    if breath_gaps > 5:
        # More gaps = more room for fills
        if verbose:
            print(f"   └─ {breath_gaps} breath gaps detected")
            print(f"   └─ Boosting drums/melody for fills")
        levels['drums'] *= 1.15
        levels['other'] *= 1.25
    
    # Combine stems with intelligent levels
    if verbose:
        print(f"\n   Final Mix Levels:")
        for name, level in levels.items():
            print(f"   • {name.capitalize()}: {level:.2f}")
    
    # Ensure all audio has same length
    max_len = max(
        vocal.shape[1],
        *(audio.shape[1] for audio in stems_audio.values())
    )
    
    def pad_to_length(audio, target_len):
        if audio.shape[1] < target_len:
            pad_width = ((0, 0), (0, target_len - audio.shape[1]))
            return np.pad(audio, pad_width, mode='constant')
        return audio[:, :target_len]
    
    vocal = pad_to_length(vocal, max_len)
    for stem_name in stems_audio:
        stems_audio[stem_name] = pad_to_length(stems_audio[stem_name], max_len)
    
    # MIX!
    final_mix = (
        vocal * levels['vocal'] +
        stems_audio.get('drums', 0) * levels['drums'] +
        stems_audio.get('bass', 0) * levels['bass'] +
        stems_audio.get('other', 0) * levels['other']
    )
    
    # Prevent clipping
    max_val = np.max(np.abs(final_mix))
    if max_val > 0.95:
        final_mix = final_mix * (0.95 / max_val)
        if verbose:
            print(f"\n   ⚠️  Applied limiting: {max_val:.2f} → 0.95")
    
    # Save mixed audio
    output_path = "mixed_vocals_and_beat.wav"
    import soundfile as sf
    sf.write(output_path, final_mix.T, sr)
    
    if verbose:
        print(f"\n✅ STEM MIXING COMPLETE: {output_path}")
    
    return output_path


# Legacy function for backward compatibility
def mix_vocal_and_beat(vocal_path: str, beat_path: str, vocal_dna: dict, verbose: bool = False) -> str:
    """
    Simple mixing without stem separation (fallback).
    """
    if verbose:
        print("\n🎚️ SIMPLE VOCAL-BEAT MIXING...")
    
    vocal, sr = librosa.load(vocal_path, sr=None, mono=False)
    beat, _ = librosa.load(beat_path, sr=sr, mono=False)
    
    if vocal.ndim == 1:
        vocal = np.stack([vocal, vocal])
    if beat.ndim == 1:
        beat = np.stack([beat, beat])
    
    # Ensure same length
    max_len = max(vocal.shape[1], beat.shape[1])
    
    def pad_to_length(audio, target_len):
        if audio.shape[1] < target_len:
            pad_width = ((0, 0), (0, target_len - audio.shape[1]))
            return np.pad(audio, pad_width, mode='constant')
        return audio[:, :target_len]
    
    vocal = pad_to_length(vocal, max_len)
    beat = pad_to_length(beat, max_len)
    
    # Simple mix
    final_mix = vocal * 1.0 + beat * 0.7
    
    # Prevent clipping
    max_val = np.max(np.abs(final_mix))
    if max_val > 0.95:
        final_mix = final_mix * (0.95 / max_val)
    
    output_path = "mixed_vocals_and_beat.wav"
    import soundfile as sf
    sf.write(output_path, final_mix.T, sr)
    
    if verbose:
        print(f"✅ Simple mixing complete: {output_path}")
    
    return output_path
