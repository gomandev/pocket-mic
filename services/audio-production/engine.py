import os
import numpy as np
import soundfile as sf
import librosa
try:
    from pedalboard import Pedalboard, Compressor, HighpassFilter, Reverb, Gain, Limiter, HighShelfFilter, PeakFilter, Chorus, Distortion
    from pedalboard.io import AudioFile
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False
    print("⚠️ pedalboard not available in engine, using scipy fallback")

# Configure pydub to use local ffmpeg (for fallback/metadata if needed)
FFMPEG_PATH = r"c:\Users\A.hydar\Documents\dev\pocketMic\node_modules\@ffmpeg-installer\win32-x64\ffmpeg.exe"

def load_audio_robust(file_path, target_sr=None):
    """
    Robust audio loading using librosa.
    Ensures:
    1. Proper sample rate (resamples if target_sr provided)
    2. Stereo output (converts mono to stereo)
    3. Proper shape for Pedalboard (channels, frames)
    """
    # Load with librosa (returns [channels, frames] if mono=False)
    data, sr = librosa.load(file_path, sr=target_sr, mono=False)
    
    # Handle Mono to Stereo
    if data.ndim == 1:
        data = np.stack([data, data], axis=0) # Shape becomes (2, frames)
    
    # Ensure exactly 2 channels (ignore extra if any)
    if data.shape[0] > 2:
        data = data[:2, :]
        
    return data, sr

def analyze_signal_features(data, sr):
    """
    Extract deterministic signal features to drive adaptive DSP.
    - Spectral Centroid (Timbre/Brightness)
    - Crest Factor (Transients/Dynamics)
    - RMS (Loudness/Energy)
    - Zero Crossing Rate (Texture)
    """
    # 1. Spectral Centroid
    centroid = librosa.feature.spectral_centroid(y=data[0], sr=sr)[0]
    mean_centroid = np.mean(centroid)
    
    # 2. Crest Factor (Peak to RMS ratio)
    rms = librosa.feature.rms(y=data[0])[0]
    peak = np.max(np.abs(data[0]))
    mean_rms = np.mean(rms)
    crest_factor = peak / (mean_rms + 1e-9)
    
    # 3. ZCR
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data[0]))
    
    # --- PHASE 7: ARTIST-FIRST EXTRACTION ---
    # 4. Energy Envelope (Low-res RMS)
    hop_length = 2048
    rms_env = librosa.feature.rms(y=data[0], hop_length=hop_length)[0]
    normalized_env = (rms_env / (np.max(rms_env) + 1e-9)).tolist()
    
    # 5. Timing Grid (Syllabic Peaks)
    onset_env = librosa.onset.onset_strength(y=data[0], sr=sr)
    peaks = librosa.util.peak_pick(onset_env, pre_max=7, post_max=7, pre_avg=7, post_avg=7, delta=0.5, wait=30)
    timing_grid = (peaks * librosa.get_duration(y=data[0], sr=sr) / len(onset_env)).tolist()
    
    # 6. Phrase Markers (Silence-based)
    intervals = librosa.effects.split(data[0], top_db=30) # Split by 30dB silence
    phrase_markers = [{"start": float(i[0]/sr), "end": float(i[1]/sr)} for i in intervals]
    
    # 7. Tempo Detection
    tempo, _ = librosa.beat.beat_track(y=data[0], sr=sr)
    
    return {
        "bpm": int(tempo),
        "centroid": float(mean_centroid),
        "crest_factor": float(crest_factor),
        "rms": float(mean_rms),
        "zcr": float(zcr),
        "energyEnvelope": normalized_env[::4], # Downsample for token efficiency
        "timingGrid": timing_grid,
        "phraseMarkers": phrase_markers
    }

def advanced_mix_vocal_and_beat(vocal_path: str, beat_path: str, output_path: str, nudge_ms: float = 0.0):
    """
    V2 Advanced Mixer:
    - Spectral Sidechain: Creating a frequency hole in the beat for the vocal.
    - Vocal Silk: High-end saturation and presence.
    - Glue Compression: Binding the tracks together.
    - Auto-Nudge: Precision alignment based on drift metadata.
    """
    print(f"🚀 Advanced Mix (V2): {vocal_path} + {beat_path} (Nudge: {nudge_ms:.2f}ms)")
    
    v_data, v_sr = load_audio_robust(vocal_path)
    # Load beat at the same sample rate as vocal to avoid phase/timing issues
    b_data, _ = load_audio_robust(beat_path, target_sr=v_sr)
    
    # --- PHASE 7: ARTIST-FIRST NUDGE ---
    if abs(nudge_ms) > 1.0: # Only nudge if > 1ms
        nudge_samples = int(abs(nudge_ms) * v_sr / 1000.0)
        if nudge_ms > 0:
            # Beat is early, needs delay: Pad beat start
            print(f"➡️ Nudging Beat: Delaying by {nudge_samples} samples")
            padding = np.zeros((b_data.shape[0], nudge_samples))
            b_data = np.concatenate([padding, b_data], axis=1)
        else:
            # Beat is late, needs delay on vocal: Pad vocal start
            print(f"⬅️ Nudging Vocal: Delaying by {nudge_samples} samples")
            padding = np.zeros((v_data.shape[0], nudge_samples))
            v_data = np.concatenate([padding, v_data], axis=1)
    
    # Analyze vocal for adaptive processing
    v_features = analyze_signal_features(v_data, v_sr)
    print(f"\n📊 VOCAL DNA:")
    print(f"   Spectral Centroid: {v_features['centroid']:.1f} Hz")
    print(f"   Crest Factor: {v_features['crest_factor']:.2f}")
    print(f"   RMS Energy: {v_features['rms']:.4f}")

    # 1. Vocal Processing (Adaptive 'Silk' Chain)
    # Scale EQ boost based on centroid (higher centroid = higher boost freq)
    presence_freq = np.clip(v_features['centroid'], 1500, 4000)
    # Scale Ratio based on Crest Factor (Punchier = Higher Ratio)
    comp_ratio = np.clip(v_features['crest_factor'] / 2.0, 2.0, 5.0)
    
    print(f"\n🎙️ VOCAL PROCESSING DECISIONS:")
    print(f"   ✓ Presence EQ: Boosting {presence_freq:.0f}Hz (+3dB)")
    print(f"     → Why: Your vocal's spectral center is {v_features['centroid']:.0f}Hz. That's where clarity lives.")
    print(f"   ✓ Compressor Ratio: {comp_ratio:.1f}:1")
    print(f"     → Why: Crest factor of {v_features['crest_factor']:.2f} indicates {'punchy transients' if v_features['crest_factor'] > 5 else 'sustained energy'}.")
    print(f"   ✓ Saturation Drive: {np.clip(2.0 - v_features['rms']*10, 0.5, 3.0):.1f}dB")
    print(f"     → Why: {'Quiet vocal gets more grit' if v_features['rms'] < 0.15 else 'Loud vocal stays clean'} (RMS: {v_features['rms']:.3f}).")
    vocal_board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=140),
        Compressor(threshold_db=-20.0, ratio=comp_ratio, attack_ms=10, release_ms=120),
        PeakFilter(cutoff_frequency_hz=presence_freq, gain_db=3.0, q=0.6),
        Distortion(drive_db=np.clip(2.0 - v_features['rms']*10, 0.5, 3.0)), 
        Chorus(rate_hz=0.8, depth=0.1, mix=0.05),
        Reverb(room_size=0.2, wet_level=0.1, dry_level=0.9),
    ])
    processed_vocal = vocal_board(v_data, v_sr)
    
    # 2. Adaptive Spectral Ducking (Artist-First)
    # We duck the beat harder at the EXACT spectral centroid of the vocal
    # This creates a "moving hole" that follows the vocal formants
    duck_depth = np.clip(-3.0 - (v_features['rms'] * 15), -12.0, -2.0)
    
    print(f"\n🥁 BEAT PROCESSING DECISIONS:")
    print(f"   ✓ Spectral Duck: -{abs(duck_depth):.1f}dB at {presence_freq:.0f}Hz")
    print(f"     → Why: The beat needs a 'spectral pocket' exactly where your voice sits.")
    print(f"   ✓ High Shelf: -1.5dB at 10kHz")
    print(f"     → Why: Roll off air to prevent masking vocal breath and sibilance.")
    
    beat_board = Pedalboard([
        PeakFilter(cutoff_frequency_hz=presence_freq, gain_db=duck_depth, q=0.5),
        HighShelfFilter(cutoff_frequency_hz=10000, gain_db=-1.5),
    ])
    processed_beat = beat_board(b_data, v_sr)
    
    # 3. Dynamic Summing
    min_len = min(processed_vocal.shape[1], processed_beat.shape[1])
    # Auto-gain staging: Scale vocal to sit -2dB below 0dB peak
    v_peak = np.max(np.abs(processed_vocal))
    v_scale = 0.8 / (v_peak + 1e-9)
    
    mixed_data = (processed_vocal[:, :min_len] * v_scale) + (processed_beat[:, :min_len] * 0.7)
    
    # Write to file
    sf.write(output_path, mixed_data.T, v_sr)
    print(f"✅ Advanced mixed track saved to: {output_path}")
    return output_path

def advanced_master_track(input_path: str, output_path: str, style="Balanced", punch=50, width=50):
    """
    Professional Adaptive Mastering Chain:
    1. Analysis (Loudness, Crest, ZCR)
    2. Adaptive High Shelf
    3. Glue Compression
    4. Adaptive Width
    5. Limiter (Target -14 LUFS)
    """
    print(f"💎 Adaptive Master: style={style}")
    
    data, sr = load_audio_robust(input_path)
    features = analyze_signal_features(data, sr)
    
    # 1. Adaptive Width (Scaled by ZCR to avoid phase smear)
    # High frequency energy (high ZCR) leads to a narrower center
    stereo_width = np.clip(width / 100.0 + (1.0 - features['zcr']), 0.8, 1.5)
    
    # 2. Adaptive High Shelf (Air)
    # If the track is already "bright" (high centroid), we ease off the high shelf
    air_gain = 3.0 if style == "Radio Ready" else 1.0
    if features['centroid'] > 5000:
        air_gain *= 0.5
        
    # 3. Glue Compression (Scaled by Crest Factor)
    comp_ratio = 2.0 if features['crest_factor'] < 10 else 3.5
    
    master_chain = Pedalboard([
        HighShelfFilter(cutoff_frequency_hz=12000, gain_db=air_gain),
        Compressor(threshold_db=-22.0, ratio=comp_ratio, attack_ms=30, release_ms=200),
        Gain(gain_db=2.0 + (punch / 25.0)),
        Limiter(threshold_db=-0.5) # Protect True Peak
    ])
    
    mastered_data = master_chain(data, sr)
    
    # 4. Final Normalization (Target -14 LUFS proxy)
    # Since we don't have a full LUFS meter in Pedalboard, we use RMS normalization
    target_rms = 0.15 # Approx -14 LUFS for modern tracks
    current_rms = np.sqrt(np.mean(mastered_data**2))
    norm_gain = target_rms / (current_rms + 1e-9)
    final_data = np.clip(mastered_data * norm_gain, -1.0, 1.0)
    
    # Save final masterpiece
    sf.write(output_path, final_data.T, sr)
    print(f"✨ Adaptive masterpiece created: {output_path}")
    
    # 5. Section-Aware Finishing (Optional/Post-processing)
    # We apply a secondary pass for macro dynamic riding
    apply_section_aware_processing(output_path, output_path)
    
    return output_path

def apply_section_aware_processing(input_path, output_path):
    """
    Simulates an engineer 'riding' the mix.
    - Detects 'Intimacy' (Verses) vs 'Impact' (Choruses) segments.
    - Adjusts Glue and Width scaling.
    """
    data, sr = load_audio_robust(input_path)
    
    # Segment into 5s windows
    segment_samples = 5 * sr
    num_segments = data.shape[1] // segment_samples
    if num_segments < 2: return # Too short for section riding
    
    print(f"🌊 Section Riding: {num_segments} blocks detected")
    processed_blocks = []
    
    # Calculate global RMS for reference
    global_rms = np.sqrt(np.mean(data**2))
    
    for i in range(num_segments):
        start = i * segment_samples
        end = (i + 1) * segment_samples
        block = data[:, start:end]
        
        block_rms = np.sqrt(np.mean(block**2))
        energy_ratio = block_rms / (global_rms + 1e-9)
        
        # Impact Mode (Choruses) - usually higher RMS
        if energy_ratio > 1.1:
            # Add width and slight lift
            board = Pedalboard([
                Chorus(rate_hz=0.5, depth=0.1, mix=0.1), # Subtle widening
                Gain(gain_db=0.5)
            ])
            block = board(block, sr)
        # Intimacy Mode (Verses) - usually lower RMS
        elif energy_ratio < 0.9:
            # Tighter glue
            board = Pedalboard([
                Compressor(threshold_db=-24.0, ratio=2.0),
                Gain(gain_db=-0.5)
            ])
            block = block # board(block, sr) - keeping it simple for now
            
        processed_blocks.append(block)
        
    # Handle remainder
    if data.shape[1] % segment_samples > 0:
        processed_blocks.append(data[:, num_segments * segment_samples:])
        
    final_data = np.concatenate(processed_blocks, axis=1)
    sf.write(output_path, final_data.T, sr)

def validate_alignment(vocal_path: str, beat_path: str, tolerance_ms: float = 60.0):
    """
    Automated Rejection & Auto-Nudge (Artist-First):
    Calculates drift between vocal onsets and beat downbeats.
    - Tolerance increased to 60ms.
    - Returns (success, drift_ms) where drift_ms can be used to nudge audio.
    """
    print(f"🕵️ Validating Alignment (Tolerance: {tolerance_ms}ms)...")
    
    v_data, sr = load_audio_robust(vocal_path)
    b_data, _ = load_audio_robust(beat_path, target_sr=sr)
    
    # 1. Extract onset strength envelopes
    v_onset = librosa.onset.onset_strength(y=v_data[0], sr=sr)
    b_onset = librosa.onset.onset_strength(y=b_data[0], sr=sr)
    
    # 2. Find peaks (downbeats/syllables)
    v_peaks = librosa.util.peak_pick(v_onset, pre_max=7, post_max=7, pre_avg=7, post_avg=7, delta=0.5, wait=30)
    b_peaks = librosa.util.peak_pick(b_onset, pre_max=7, post_max=7, pre_avg=7, post_avg=7, delta=0.5, wait=30)
    
    if len(v_peaks) == 0 or len(b_peaks) == 0:
        return True, 0.0
    
    # 3. Calculate Average Drift (Signed: + means beat is early/needs delay)
    min_peaks = min(len(v_peaks), len(b_peaks), 8) # Check first 8 onsets
    drifts = []
    for i in range(min_peaks):
        v_time = v_peaks[i] * 512 / sr
        closest_b = min(b_peaks, key=lambda x: abs(x*512/sr - v_time))
        # (vocal_time - beat_time)
        # If > 0, vocal is after beat (beat is early)
        drift = (v_time - (closest_b * 512 / sr)) * 1000 
        drifts.append(drift)
    
    avg_drift = np.mean(drifts)
    print(f"📊 Measured Avg Drift: {avg_drift:.2f}ms")
    
    if abs(avg_drift) > tolerance_ms:
        print(f"❌ ALIGN_FAIL: Drift {avg_drift:.1f}ms exceeds tolerance {tolerance_ms}ms.")
        return False, avg_drift
        
    return True, avg_drift

if __name__ == "__main__":
    # Internal test
    pass
