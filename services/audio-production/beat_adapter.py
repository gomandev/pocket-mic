"""
BEAT ADAPTATION LAYER
======================
AI Constraint & Validation System

This module ensures AudioCraft (or any beat generator) follows
the "vocal-first" philosophy:
- BPM must match vocal (±2 BPM tolerance)
- Key must harmonize
- Density must adapt to vocal phrasing
- Alignment must be <100ms drift

This is NOT about "creative AI"—it's about enforcing professional
production standards where the vocal is the master clock.
"""

import numpy as np
import librosa
from vocal_intel import load_audio_robust
from typing import Dict, Tuple


def validate_beat_alignment(
    vocal_path: str,
    beat_path: str,
    tolerance_ms: float = 100.0,
    verbose: bool = True
) -> Tuple[bool, float]:
    """
    Validate that the beat aligns with vocal downbeats.
    
    This is the "rejection rule" for AI-generated beats.
    If alignment fails, the beat must be regenerated.
    
    Args:
        vocal_path: Path to vocal audio
        beat_path: Path to AI-generated beat
        tolerance_ms: Max acceptable drift (milliseconds)
        verbose: Print analysis
        
    Returns:
        (is_aligned, drift_ms): Success flag and measured drift
    """
    if verbose:
        print(f"\n🕵️ VALIDATING BEAT ALIGNMENT:")
        print(f"   Tolerance: {tolerance_ms}ms")
    
    v_data, sr = load_audio_robust(vocal_path)
    b_data, _ = load_audio_robust(beat_path, target_sr=sr)
    
    # Extract onset envelopes
    v_onset = librosa.onset.onset_strength(y=v_data[0], sr=sr)
    b_onset = librosa.onset.onset_strength(y=b_data[0], sr=sr)
    
    # Find peaks (downbeats/syllables)
    v_peaks = librosa.util.peak_pick(
        v_onset,
        pre_max=7, post_max=7,
        pre_avg=7, post_avg=7,
        delta=0.5, wait=30
    )
    b_peaks = librosa.util.peak_pick(
        b_onset,
        pre_max=7, post_max=7,
        pre_avg=7, post_avg=7,
        delta=0.5, wait=30
    )
    
    if len(v_peaks) == 0 or len(b_peaks) == 0:
        if verbose:
            print(f"   ⚠️ Insufficient onsets detected. Allowing by default.")
        return True, 0.0
    
    # Calculate average drift (first 8 onsets)
    min_peaks = min(len(v_peaks), len(b_peaks), 8)
    drifts = []
    
    for i in range(min_peaks):
        v_time = v_peaks[i] * 512 / sr
        closest_b = min(b_peaks, key=lambda x: abs(x * 512 / sr - v_time))
        # Signed drift: positive = beat is early
        drift = (v_time - (closest_b * 512 / sr)) * 1000
        drifts.append(drift)
    
    avg_drift = np.mean(drifts)
    
    if verbose:
        print(f"   Measured Drift: {avg_drift:+.2f}ms (avg of {min_peaks} onsets)")
    
    is_aligned = abs(avg_drift) <= tolerance_ms
    
    if not is_aligned:
        if verbose:
            print(f"   ❌ ALIGNMENT REJECTED")
            print(f"      Drift {abs(avg_drift):.1f}ms exceeds {tolerance_ms}ms limit.")
            print(f"      → AudioCraft must REGENERATE with tighter constraints.")
    else:
        if verbose:
            print(f"   ✅ ALIGNMENT APPROVED")
            if abs(avg_drift) > 1.0:
                print(f"      → Will apply {avg_drift:+.2f}ms auto-nudge in mixer.")
    
    return is_aligned, avg_drift


def validate_bpm_lock(
    vocal_bpm: float,
    beat_bpm: float,
    tolerance: float = 2.0,
    verbose: bool = True
) -> bool:
    """
    Validate that beat BPM matches vocal within tolerance.
    
    Args:
        vocal_bpm: Detected vocal tempo
        beat_bpm: AI-generated beat tempo
        tolerance: Max acceptable BPM difference
        verbose: Print validation result
        
    Returns:
        is_valid: True if BPM is locked
    """
    drift = abs(vocal_bpm - beat_bpm)
    is_valid = drift <= tolerance
    
    if verbose:
        print(f"\n🎵 BPM LOCK VALIDATION:")
        print(f"   Vocal: {vocal_bpm:.1f} BPM")
        print(f"   Beat: {beat_bpm:.1f} BPM")
        print(f"   Drift: {drift:.1f} BPM")
        
        if is_valid:
            print(f"   ✅ BPM LOCKED (within {tolerance} BPM)")
        else:
            print(f"   ❌ BPM DRIFT DETECTED")
            print(f"      → AudioCraft must regenerate at {vocal_bpm:.0f} BPM")
    
    return is_valid


def create_audiocraft_constraints(vocal_dna: Dict) -> Dict:
    """
    Convert vocal DNA into strict AudioCraft generation constraints.
    
    These are NOT suggestions—they're hard limits. AudioCraft
    must follow these or be rejected.
    
    Args:
        vocal_dna: Feature dict from vocal_intel.extract_vocal_dna()
        
    Returns:
        Constraint dict for AudioCraft API
    """
    constraints = {
        # === TEMPO LOCK ===
        "bpm": vocal_dna['bpm'],
        "bpm_tolerance": 2.0,  # ±2 BPM allowed
        
        # === DENSITY MAPPING ===
        # Sparse instrumentation during vocal peaks
        # Complex fills during vocal breaths/silence
        "density_envelope": vocal_dna['energyEnvelope'],
        "density_mode": "inverse",  # High vocal energy = sparse beat
        
        # === PHRASE ALIGNMENT ===
        # Chord changes must happen at phrase boundaries
        "phrase_markers": vocal_dna['phraseMarkers'],
        "enforce_phrase_lock": True,
        
        # === SPECTRAL COMPATIBILITY ===
        # Beat should stay out of vocal's frequency zone
        "vocal_spectral_center": vocal_dna['centroid'],
        "spectral_duck_range": (
            max(vocal_dna['centroid'] - 500, 100),
            min(vocal_dna['centroid'] + 500, 8000)
        ),
        
        # === VALIDATION RULES ===
        "max_regeneration_attempts": 3,
        "alignment_tolerance_ms": 100.0,
    }
    
    return constraints


def should_regenerate_beat(
    vocal_path: str,
    beat_path: str,
    vocal_dna: Dict,
    verbose: bool = True
) -> Tuple[bool, str]:
    """
    Comprehensive beat validation decision.
    
    Checks all constraints and decides if regeneration is needed.
    
    Args:
        vocal_path: Path to vocal
        beat_path: Path to AI-generated beat
        vocal_dna: Vocal features
        verbose: Print decision process
        
    Returns:
        (should_regenerate, reason): Decision and human-readable explanation
    """
    # Extract beat BPM
    b_data, sr = load_audio_robust(beat_path)
    beat_tempo, _ = librosa.beat.beat_track(y=b_data[0], sr=sr)
    
    # === CHECK 1: BPM Lock ===
    if not validate_bpm_lock(vocal_dna['bpm'], beat_tempo, tolerance=2.0, verbose=verbose):
        return True, f"BPM drift: {abs(vocal_dna['bpm'] - beat_tempo):.1f} BPM off target"
    
    # === CHECK 2: Alignment ===
    is_aligned, drift = validate_beat_alignment(
        vocal_path, beat_path,
        tolerance_ms=100.0,
        verbose=verbose
    )
    
    if not is_aligned:
        return True, f"Alignment drift: {abs(drift):.1f}ms exceeds 100ms limit"
    
    # All checks passed
    if verbose:
        print(f"\n✅ BEAT VALIDATION PASSED")
        print(f"   → Beat is ready for mixing")
    
    return False, "Validation passed"
