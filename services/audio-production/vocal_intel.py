"""
VOCAL INTELLIGENCE LAYER
========================
Producer-First Feature Extraction

This module extracts the "producer's perspective" from raw vocals:
- Deterministic rhythm & timing analysis
- Spectral fingerprinting (brightness, warmth, character)
- Dynamic profiling (transients, sustain, energy)
- Phrase structure detection

Every extraction is explainable and rooted in signal processing,
not AI randomness.
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple

def load_audio_robust(file_path: str, target_sr: int = None) -> Tuple[np.ndarray, int]:
    """
    Robust audio loading with stereo normalization.
    
    Args:
        file_path: Path to audio file
        target_sr: Target sample rate (None = preserve original)
        
    Returns:
        (data, sr): Stereo audio data [channels, samples] and sample rate
    """
    data, sr = librosa.load(file_path, sr=target_sr, mono=False)
    
    # Ensure stereo
    if data.ndim == 1:
        data = np.stack([data, data], axis=0)
    
    # Limit to 2 channels
    if data.shape[0] > 2:
        data = data[:2, :]
        
    return data, sr


def detect_breath_gaps(audio: np.ndarray, sr: int, hop_length: int = 512) -> Tuple[List[Dict], List[float]]:
    """
    Detect breath/silence gaps with precision for dynamic arrangement.
    
    This is critical for "breathing" instrumentation - music fills the gaps.
    
    Args:
        audio: Mono audio signal
        sr: Sample rate
        hop_length: Frame size for analysis
        
    Returns:
        (breath_gaps, presence_envelope):
        - breath_gaps: List of {start, end, duration} in seconds
        - presence_envelope: Frame-by-frame vocal activity (0.0-1.0)
    """
    # Calculate RMS energy with tight frames for precision
    rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
    
    # Adaptive threshold: 20th percentile (catches even quiet breaths)
    threshold = np.percentile(rms, 20)
    
    # Smooth the RMS to avoid choppy detection
    from scipy.ndimage import gaussian_filter1d
    rms_smooth = gaussian_filter1d(rms, sigma=2)
    
    # Binary mask: 1 = singing, 0 = silence/breath
    is_vocal = rms_smooth > threshold
    
    # Normalize RMS to 0-1 range for presence envelope
    rms_norm = (rms_smooth - rms_smooth.min()) / (rms_smooth.max() - rms_smooth.min() + 1e-9)
    
    # Find breath gaps (contiguous silence regions)
    breath_gaps = []
    in_gap = False
    gap_start = 0
    
    frame_duration = hop_length / sr
    
    for i, is_singing in enumerate(is_vocal):
        if not is_singing and not in_gap:
            # Start of a breath gap
            gap_start = i
            in_gap = True
        elif is_singing and in_gap:
            # End of a breath gap
            gap_end = i
            gap_duration = (gap_end - gap_start) * frame_duration
            
            # Only log significant gaps (>100ms)
            if gap_duration > 0.1:
                breath_gaps.append({
                    "start": gap_start * frame_duration,
                    "end": gap_end * frame_duration,
                    "duration": gap_duration
                })
            in_gap = False
    
    return breath_gaps, rms_norm.tolist()


def extract_vocal_dna(file_path: str, verbose: bool = True) -> Dict:
    """
    Extract complete vocal DNA for production decisions.
    
    This is the foundational analysis that drives all downstream processing.
    Each feature is deterministic and explainable.
    
    Returns:
        Vocal DNA dict with:
        - bpm: Detected tempo
        - timingGrid: Syllabic onset times (seconds)
        - phraseMarkers: Speech/silence boundaries
        - energyEnvelope: Frame-by-frame RMS curve
        - centroid: Spectral brightness (Hz)
        - crest_factor: Peak-to-RMS ratio (dynamics)
        - rms: Average loudness
        - zcr: Zero-crossing rate (texture/noisiness)
        - breath_gaps: Silence moments for instrumental fills
        - density_envelope: Inverse presence (for breathing arrangement)
    """
    data, sr = load_audio_robust(file_path)
    
    if verbose:
        print(f"\n🔬 EXTRACTING VOCAL DNA...")
        print(f"   Sample Rate: {sr}Hz")
        print(f"   Duration: {len(data[0])/sr:.2f}s")
    
    # === RHYTHM & TIMING ===
    tempo, _ = librosa.beat.beat_track(y=data[0], sr=sr)
    
    onset_env = librosa.onset.onset_strength(y=data[0], sr=sr)
    peaks = librosa.util.peak_pick(
        onset_env, 
        pre_max=7, post_max=7, 
        pre_avg=7, post_avg=7, 
        delta=0.5, wait=30
    )
    timing_grid = (peaks * librosa.get_duration(y=data[0], sr=sr) / len(onset_env)).tolist()
    
    # === PHRASE STRUCTURE ===
    intervals = librosa.effects.split(data[0], top_db=30)
    phrase_markers = [
        {"start": float(i[0]/sr), "end": float(i[1]/sr)} 
        for i in intervals
    ]
    
    # === ENERGY ENVELOPE ===
    hop_length = 2048
    rms_env = librosa.feature.rms(y=data[0], hop_length=hop_length)[0]
    normalized_env = (rms_env / (np.max(rms_env) + 1e-9)).tolist()
    
    # === SPECTRAL FINGERPRINT ===
    centroid = librosa.feature.spectral_centroid(y=data[0], sr=sr)[0]
    mean_centroid = float(np.mean(centroid))
    
    # === DYNAMIC CHARACTER ===
    rms = librosa.feature.rms(y=data[0])[0]
    peak = np.max(np.abs(data[0]))
    mean_rms = float(np.mean(rms))
    crest_factor = float(peak / (mean_rms + 1e-9))
    
    # === TEXTURE ===
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=data[0])))
    
    # === BREATH GAPS & DENSITY ENVELOPE (Professional Breathing Arrangement) ===
    breath_gaps, presence_envelope = detect_breath_gaps(data[0], sr)
    
    # Inverse density: when vocal is loud, beat should be sparse
    # This creates the "breathing" effect professionals use
    density_envelope = [1.0 - p for p in presence_envelope]
    
    if verbose:
        print(f"\n✅ VOCAL DNA EXTRACTED:")
        print(f"   Tempo: {int(tempo)} BPM")
        print(f"   Timing Peaks: {len(timing_grid)} syllabic onsets")
        print(f"   Phrases: {len(phrase_markers)} segments")
        print(f"   Breath Gaps: {len(breath_gaps)} silence moments (for fills)")
        print(f"   Spectral Center: {mean_centroid:.0f}Hz")
        print(f"   Crest Factor: {crest_factor:.2f} ({'punchy' if crest_factor > 5 else 'sustained'})")
        print(f"   Average RMS: {mean_rms:.4f}")
    
    return {
        "bpm": int(tempo),
        "timingGrid": timing_grid,
        "phraseMarkers": phrase_markers,
        "energyEnvelope": normalized_env[::4],  # Downsample for efficiency
        "centroid": mean_centroid,
        "crest_factor": crest_factor,
        "rms": mean_rms,
        "zcr": zcr,
        "breath_gaps": breath_gaps,
        "density_envelope": density_envelope[::8]  # Downsample for efficiency
    }
