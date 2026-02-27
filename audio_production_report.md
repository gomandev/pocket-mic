# 🎙️ PocketMic: Advanced Audio Production Report (V2 Engine)

This report details the implementation of the **V2 Advanced Audio Engine** for PocketMic, an AI-first audio production studio. The engine is designed to bridge the gap between AI-generated beats and raw vocal takes using professional-grade DSP techniques.

---

## 🏗️ Project Context
- **Product**: PocketMic - A single-click AI Studio.
- **Tech Stack**: Next.js (Frontend), FastAPI (Production Service), Supabase (Storage/DB), Replicate (AI Beat Generation).
- **Core Challenge**: Integrating a highly variable AI-generated beat with a raw vocal take to produce a "radio-ready" final master without human intervention.

---

## 💎 The V2 Advanced Engineering Algorithm
The heart of our production is the `engine.py` module, which utilizes **Spotify's Pedalboard** and **Librosa** for high-precision audio manipulation.

### 1. Robust Audio Normalization (`load_audio_robust`)
- **Resampling**: Automatically resamples all assets to a unified target sample rate (matches the vocal take) using `librosa`.
- **Stereo Broadcasting**: Ensures all inputs are stereo by stacking mono channels, preventing phase cancellation and mapping issues in the DSP pipeline.

### 2. The "PocketPocket" Spectral Sidechain
Unlike simple volume ducking, we implement **Static Spectral Sidechaining**:
- **Mechanism**: A high-precision `PeakFilter` is applied to the AI beat at **2.0kHz (Q=0.4)** with a **-4.0dB** dip.
- **Objective**: This carves out a "sonic pocket" specifically for the vocal's clarity and presence range, allowing the voice to sit "inside" the beat rather than on top of it.

### 3. The "Vocal Silk" Chain
To make raw recordings sound expensive, we apply a multi-stage serial chain:
- **Cleanups**: High-pass filter at 140Hz to remove sub-harmonic rumble.
- **Symmetry**: Compression at 3.5:1 ratio for consistent vocal leveling.
- **Silk Saturation**: A subtle 1.5dB `Distortion` drive and a +2.5dB boost at 2.5kHz for harmonic "sheen" and digital presence.
- **Spatial Glue**: Sub-perceptual `Chorus` (5% mix) and a tight `Reverb` (20% room size) to bind the dry vocal to the AI-generated acoustic space.

### 4. Stylistic AI Mastering
Users can transition between three distinct "Sonic Personalities":
- **Radio Ready**: Focused on "Air" (+10kHz) and Glue Compression (2.0:1) to mimic pop production standards.
- **Warmer**: Softens the high-end (-2dB @ 8kHz) and adds low-mid warmth (+1.5dB @ 400Hz) with tube-style saturation.
- **Club Punch**: Emphasizes sub-harmonics (+3dB @ 60kHz) and applies a "Hard Squeeze" (4.0:1 ratio) for maximum energy.

---

## 🐍 Current Implementation (`engine.py`)
```python
import os
import numpy as np
import soundfile as sf
import librosa
from pedalboard import Pedalboard, Compressor, HighpassFilter, Reverb, Gain, Limiter, HighShelfFilter, PeakFilter, Chorus, Distortion

def advanced_mix_vocal_and_beat(vocal_path, beat_path, output_path):
    v_data, v_sr = load_audio_robust(vocal_path)
    b_data, _ = load_audio_robust(beat_path, target_sr=v_sr)
    
    # Vocal Silk Chain
    vocal_board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=140),
        Compressor(threshold_db=-18.0, ratio=3.5, attack_ms=15, release_ms=100),
        PeakFilter(cutoff_frequency_hz=2500, gain_db=2.5, q=0.7),
        Distortion(drive_db=1.5),
        Chorus(rate_hz=0.8, depth=0.1, mix=0.05),
        Reverb(room_size=0.2, wet_level=0.1, dry_level=0.9),
    ])
    processed_vocal = vocal_board(v_data, v_sr)
    
    # Spectral Ducking
    beat_board = Pedalboard([
        PeakFilter(cutoff_frequency_hz=2000, gain_db=-4.0, q=0.4),
        HighShelfFilter(cutoff_frequency_hz=8000, gain_db=-1.0),
    ])
    processed_beat = beat_board(b_data, b_sr=v_sr)
    
    # Summing
    min_len = min(processed_vocal.shape[1], processed_beat.shape[1])
    mixed_data = (processed_vocal[:, :min_len] * 1.1) + processed_beat[:, :min_len]
    sf.write(output_path, mixed_data.T, v_sr)
```

---

## 🚀 Expansion Brainstorming (For ChatGPT Review)
We are looking to expand this system into a "True AI Engineer." Areas for exploration:
1. **Dynamic Spectral Sidechaining**: Analyzing the vocal's real-time FFT and applying a moving dip filter to the beat that follows the singer's fundamental frequencies.
2. **AI-Driven Transient Shaping**: Detecting drum hits in the AI beat and sharpening their transients while softening them during vocal peaks.
3. **Sentiment-Aware Mastering**: Using an LLM to analyze the lyrics/vocal mood and automatically switching between "Obsidian" and "Diamond" mastering styles.
4. **Intelligent Width Scaling**: Dynamically widening the stereo image of the beat during choruses while keeping the verse mono-centered for "impact jumps."
