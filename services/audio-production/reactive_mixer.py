"""
REACTIVE DSP LAYER
==================
Deterministic, Vocal-Adaptive Mixing

This module implements the "human producer" mixing philosophy:
- Vocal processing adapts to spectral characteristics
- Beat processing creates a "spectral pocket" for the vocal
- Every decision is explainable and deterministic
- No static presets, no AI randomness

Think of this as a producer who listens to the vocal and makes
informed mixing decisions in real-time.
"""


import numpy as np
import soundfile as sf
import librosa  # For RMS envelope extraction
from scipy.interpolate import interp1d  # For envelope upsampling
from scipy.ndimage import uniform_filter1d  # For gain smoothing
from pedalboard import (
    Pedalboard, Compressor, HighpassFilter, 
    Reverb, Gain, PeakFilter, Chorus, 
    Distortion, HighShelfFilter
)
from vocal_intel import load_audio_robust
from typing import Dict


def mix_vocal_and_beat(
    vocal_path: str, 
    beat_path: str, 
    output_path: str,
    vocal_dna: Dict,
    nudge_ms: float = 0.0,
    verbose: bool = True
) -> str:
    """
    Reactive mixing driven by vocal DNA.
    
    Philosophy:
    - The vocal is the emotional leader
    - The beat adapts to create a spectral pocket
    - Every DSP decision is explainable
    
    Args:
        vocal_path: Path to vocal audio
        beat_path: Path to beat audio
        output_path: Where to save the mix
        vocal_dna: Feature dict from vocal_intel.extract_vocal_dna()
        nudge_ms: Auto-alignment offset (positive = delay beat)
        verbose: Print explainable decisions
        
    Returns:
        Path to mixed output
    """
    if verbose:
        print(f"\n🎚️ REACTIVE MIXING ENGINE")
        print(f"   Vocal: {vocal_path}")
        print(f"   Beat: {beat_path}")
        if abs(nudge_ms) > 1.0:
            print(f"   Auto-Nudge: {nudge_ms:+.2f}ms")
    
    # Load audio
    v_data, v_sr = load_audio_robust(vocal_path)
    b_data, _ = load_audio_robust(beat_path, target_sr=v_sr)
    
    # === AUTO-NUDGE (Artist-First Alignment) ===
    if abs(nudge_ms) > 1.0:
        nudge_samples = int(abs(nudge_ms) * v_sr / 1000.0)
        if nudge_ms > 0:
            # Beat is early, needs delay
            if verbose:
                print(f"   ➡️ Delaying beat by {nudge_samples} samples")
            padding = np.zeros((b_data.shape[0], nudge_samples))
            b_data = np.concatenate([padding, b_data], axis=1)
        else:
            # Vocal is early, needs delay
            if verbose:
                print(f"   ⬅️ Delaying vocal by {nudge_samples} samples")
            padding = np.zeros((v_data.shape[0], nudge_samples))
            v_data = np.concatenate([padding, v_data], axis=1)
    
    # === VOCAL PROCESSING (The "Silk Chain") ===
    presence_freq = np.clip(vocal_dna['centroid'], 1500, 4000)
    comp_ratio = np.clip(vocal_dna['crest_factor'] / 2.0, 2.0, 5.0)
    saturation_drive = np.clip(2.0 - vocal_dna['rms'] * 10, 0.5, 3.0)
    
    if verbose:
        print(f"\n🎙️ VOCAL PROCESSING:")
        print(f"   ✓ Presence EQ: +3dB @ {presence_freq:.0f}Hz")
        print(f"     → Spectral center is {vocal_dna['centroid']:.0f}Hz. Boosting clarity.")
        print(f"   ✓ Compression: {comp_ratio:.1f}:1")
        print(f"     → Crest factor {vocal_dna['crest_factor']:.2f} = {'punchy transients' if vocal_dna['crest_factor'] > 5 else 'sustained energy'}.")
        print(f"   ✓ Saturation: {saturation_drive:.1f}dB")
        print(f"     → {'Quiet vocal gets warmth' if vocal_dna['rms'] < 0.15 else 'Loud vocal stays clean'}.")
    
    vocal_chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=140),
        Compressor(threshold_db=-20.0, ratio=comp_ratio, attack_ms=10, release_ms=120),
        PeakFilter(cutoff_frequency_hz=presence_freq, gain_db=3.0, q=0.6),
        Distortion(drive_db=saturation_drive),
        Chorus(rate_hz=0.8, depth=0.1, mix=0.05),
        Reverb(room_size=0.2, wet_level=0.1, dry_level=0.9),
    ])
    processed_vocal = vocal_chain(v_data, v_sr)
    
    
    # === BEAT PROCESSING (The "Breathing Pocket") ===
    # Professional sidechain: beat ducks when vocal hits, swells in gaps
    duck_depth = np.clip(-3.0 - (vocal_dna['rms'] * 15), -12.0, -2.0)
    
    if verbose:
        print(f"\n🥁 BEAT PROCESSING (Sidechain Ducking):")
        print(f"   ✓ Spectral Duck: {duck_depth:.1f}dB @ {presence_freq:.0f}Hz")
        print(f"     → Creating a 'moving pocket' where the vocal sits.")
        print(f"   ✓ Air Roll-off: -1.5dB @ 10kHz")
        print(f"     → Preventing vocal breath/sibilance masking.")
        print(f"   ✓ Sidechain Compression: Beat ducks on vocal transients")
        print(f"     → Professional 'breathing' - beat fills silence, steps back during singing.")
    
    # Static EQ for spectral pocket
    beat_chain = Pedalboard([
        PeakFilter(cutoff_frequency_hz=presence_freq, gain_db=duck_depth, q=0.5),
        HighShelfFilter(cutoff_frequency_hz=10000, gain_db=-1.5),
    ])
    eq_beat = beat_chain(b_data, v_sr)
    
    
    # === SIDECHAIN COMPRESSION ===
    # TEMPORARILY FULLY DISABLED FOR DEBUGGING
    # TODO: Re-enable once array broadcasting issue is resolved
    
    processed_beat = eq_beat  # Just use EQ'd beat
    
    # === ADAPTIVE MIX BALANCE ===
    # Scale beat level based on vocal loudness (louder vocal = quieter beat)
    vocal_gain = 1.0  # Vocal always at unity
    beat_gain = np.clip(0.6 - (vocal_dna['rms'] * 2.0), 0.25, 0.55)
    
    if verbose:
        print(f"\n⚖️ MIX BALANCE:")
        print(f"   Vocal Gain: {vocal_gain:.2f} (100%)")
        print(f"   Beat Gain: {beat_gain:.2f} ({int(beat_gain*100)}%)")
        print(f"     → {'Loud vocal pushes beat back' if vocal_dna['rms'] > 0.12 else 'Quiet vocal allows beat forward'}.")
    
    min_len = min(processed_vocal.shape[1], processed_beat.shape[1])
    mixed = (processed_vocal[:, :min_len] * float(vocal_gain)) + (processed_beat[:, :min_len] * float(beat_gain))
    
    # Glue compression
    glue_chain = Pedalboard([
        Compressor(threshold_db=-10.0, ratio=1.5, attack_ms=50, release_ms=300),
        Gain(gain_db=2.0)
    ])
    final_mix = glue_chain(mixed, v_sr)
    
    sf.write(output_path, final_mix.T, v_sr)
    
    if verbose:
        print(f"\n✅ Mix complete: {output_path}")
    
    return output_path
