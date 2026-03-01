"""
REACTIVE DSP LAYER V3
=====================
Deterministic, Vocal-Adaptive Mixing with STFT Spectral Ducking

This module implements the "human producer" mixing philosophy:
- Vocal processing adapts to spectral characteristics
- STFT spectral ducking creates a MOVING frequency pocket (V3)
- Dynamic sidechain compression for amplitude breathing (V3)
- Every decision is explainable and deterministic
- No static presets, no AI randomness

V3 Upgrades:
- apply_stft_spectral_duck: Frame-by-frame frequency carving that
  follows the vocal's formant trajectory
- apply_dynamic_sidechain: Professional gain ducking with attack/release
  smoothing driven by vocal RMS envelope
"""


import numpy as np
import soundfile as sf
import librosa  # For RMS/STFT/onset extraction
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
    
    # Static EQ for base spectral pocket
    beat_chain = Pedalboard([
        PeakFilter(cutoff_frequency_hz=presence_freq, gain_db=duck_depth, q=0.5),
        HighShelfFilter(cutoff_frequency_hz=10000, gain_db=-1.5),
    ])
    eq_beat = beat_chain(b_data, v_sr)
    
    
    # === V3: STFT SPECTRAL DUCKING ===
    # Frame-by-frame frequency carving: wherever the vocal has energy,
    # the beat is attenuated at those exact frequencies.
    if verbose:
        print(f"\n🔬 STFT SPECTRAL DUCKING:")
        print(f"   → Frame-by-frame frequency carving (V3 upgrade)")
    
    spectral_ducked_beat = apply_stft_spectral_duck(
        processed_vocal, eq_beat, v_sr,
        duck_db=-3.0,  # Lighter touch since Lyria already handles density
        verbose=verbose
    )
    
    # === V3: DYNAMIC SIDECHAIN COMPRESSION ===
    # Beat amplitude tracks inverse of vocal energy with attack/release smoothing
    if verbose:
        print(f"\n🫀 DYNAMIC SIDECHAIN:")
        print(f"   → Beat breathes with vocal (V3 upgrade)")
    
    processed_beat = apply_dynamic_sidechain(
        processed_vocal, spectral_ducked_beat, v_sr,
        attack_ms=5.0, release_ms=80.0,
        floor_gain=0.35,  # Beat never drops below 35% (keeps presence)
        verbose=verbose
    )
    
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


# ==========================================================================
# V3 UPGRADE FUNCTIONS
# ==========================================================================

def apply_stft_spectral_duck(
    vocal: np.ndarray,
    beat: np.ndarray,
    sr: int,
    duck_db: float = -3.0,
    n_fft: int = 2048,
    hop_length: int = 512,
    verbose: bool = False
) -> np.ndarray:
    """
    STFT-domain spectral ducking: frame-by-frame frequency carving.
    
    Wherever the vocal has energy in the spectrum, the beat is attenuated
    at those exact frequencies in that exact frame. The result is a "moving
    hole" that follows the vocal's formant trajectory.
    
    Args:
        vocal: Processed vocal audio [channels, samples]
        beat: Beat audio to duck [channels, samples]
        sr: Sample rate
        duck_db: Attenuation in dB where vocal is loudest (negative)
        n_fft: FFT window size
        hop_length: Hop between frames
        verbose: Print decisions
        
    Returns:
        Spectrally ducked beat audio [channels, samples]
    """
    # Work on mono for STFT analysis, apply to both channels
    min_len = min(vocal.shape[1], beat.shape[1])
    vocal_mono = vocal[0, :min_len]
    
    # Compute vocal STFT
    V = librosa.stft(vocal_mono, n_fft=n_fft, hop_length=hop_length)
    V_mag = np.abs(V)
    
    # Normalize vocal magnitude to [0, 1]
    V_max = V_mag.max() + 1e-9
    V_norm = V_mag / V_max
    
    # Convert duck_db to linear scale
    duck_linear = 10 ** (duck_db / 20.0)
    
    # Create dynamic gain mask:
    # Where vocal is silent → gain = 1.0 (beat untouched)
    # Where vocal is loud → gain = duck_linear (beat attenuated)
    gain_mask = 1.0 - V_norm * (1.0 - duck_linear)
    
    # Process each channel
    ducked_channels = []
    for ch in range(beat.shape[0]):
        B = librosa.stft(beat[ch, :min_len], n_fft=n_fft, hop_length=hop_length)
        
        # Align frames (beat STFT might have different number of frames)
        min_frames = min(B.shape[1], gain_mask.shape[1])
        B_ducked = B[:, :min_frames] * gain_mask[:, :min_frames]
        
        # Reconstruct
        ducked_ch = librosa.istft(B_ducked, hop_length=hop_length, length=min_len)
        ducked_channels.append(ducked_ch)
    
    result = np.stack(ducked_channels)
    
    # Pad back to original beat length if needed
    if result.shape[1] < beat.shape[1]:
        padding = np.zeros((beat.shape[0], beat.shape[1] - result.shape[1]))
        result = np.concatenate([result, padding], axis=1)
    
    if verbose:
        active_frames = np.sum(V_norm.mean(axis=0) > 0.1)
        total_frames = V_norm.shape[1]
        print(f"   ✓ Ducking active in {active_frames}/{total_frames} frames ({100*active_frames/total_frames:.0f}%)")
        print(f"   ✓ Max attenuation: {duck_db:.1f}dB at vocal peaks")
    
    return result


def apply_dynamic_sidechain(
    vocal: np.ndarray,
    beat: np.ndarray,
    sr: int,
    attack_ms: float = 5.0,
    release_ms: float = 80.0,
    floor_gain: float = 0.35,
    hop_length: int = 512,
    verbose: bool = False
) -> np.ndarray:
    """
    Professional dynamic sidechain: beat ducks when vocal hits, swells in gaps.
    
    Uses the vocal's RMS envelope as a gain control signal with proper
    attack/release smoothing to prevent pumping artifacts.
    
    Args:
        vocal: Processed vocal audio [channels, samples]
        beat: Beat audio to duck [channels, samples]
        sr: Sample rate
        attack_ms: How fast the beat ducks (lower = faster)
        release_ms: How fast the beat swells back (higher = smoother)
        floor_gain: Minimum beat gain (0.0 = full duck, 1.0 = no duck)
        hop_length: Analysis frame size
        verbose: Print decisions
        
    Returns:
        Sidechained beat audio [channels, samples]
    """
    min_len = min(vocal.shape[1], beat.shape[1])
    
    # Extract vocal RMS energy envelope
    vocal_rms = librosa.feature.rms(y=vocal[0, :min_len], hop_length=hop_length)[0]
    
    # Invert and normalize: loud vocal → low gain, silence → full gain
    rms_max = np.max(vocal_rms) + 1e-9
    inverse_env = 1.0 - (vocal_rms / rms_max)
    
    # Apply attack/release smoothing (prevents pumping artifacts)
    attack_coeff = np.exp(-1.0 / max(1e-9, (attack_ms * sr / (1000.0 * hop_length))))
    release_coeff = np.exp(-1.0 / max(1e-9, (release_ms * sr / (1000.0 * hop_length))))
    
    smoothed = np.zeros_like(inverse_env)
    smoothed[0] = inverse_env[0]
    
    for i in range(1, len(inverse_env)):
        if inverse_env[i] < smoothed[i - 1]:
            # Attack (ducking) — fast
            smoothed[i] = attack_coeff * smoothed[i - 1] + (1 - attack_coeff) * inverse_env[i]
        else:
            # Release (swelling back) — slow
            smoothed[i] = release_coeff * smoothed[i - 1] + (1 - release_coeff) * inverse_env[i]
    
    # Scale gain curve: floor_gain at maximum duck, 1.0 at full swell
    gain_curve = floor_gain + smoothed * (1.0 - floor_gain)
    
    # Upsample gain curve to sample-level
    frame_times = np.arange(len(gain_curve)) * hop_length
    sample_times = np.arange(min_len)
    gain_samples = np.interp(sample_times, frame_times, gain_curve)
    
    # Apply to all channels of beat
    result = beat[:, :min_len] * gain_samples[np.newaxis, :]
    
    # Pad back to original length if needed
    if result.shape[1] < beat.shape[1]:
        padding = beat[:, min_len:]
        result = np.concatenate([result, padding], axis=1)
    
    if verbose:
        avg_gain = np.mean(gain_samples)
        min_gain = np.min(gain_samples)
        print(f"   ✓ Avg beat gain: {avg_gain:.2f} ({int(avg_gain*100)}%)")
        print(f"   ✓ Max duck: {min_gain:.2f} ({int(min_gain*100)}%)")
        print(f"   ✓ Attack: {attack_ms:.0f}ms / Release: {release_ms:.0f}ms")
    
    return result
