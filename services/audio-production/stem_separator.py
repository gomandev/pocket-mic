"""
AI Stem Separation using Demucs (Meta AI)
Separates audio into individual stems for intelligent mixing
"""
import replicate
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def separate_beat_stems(beat_path: str, verbose: bool = False) -> dict:
    """
    Separate generated beat into stems using Demucs AI.
    
    Uses Meta's Demucs model to extract:
    - Drums: All percussion elements
    - Bass: Low-end foundation
    - Other: Melody/harmony (keys, synths, guitars)
    
    Args:
        beat_path: Path to beat audio file
        verbose: Print detailed progress
    
    Returns:
        dict with keys: 'drums', 'bass', 'other' (paths to stem files)
    """
    if verbose:
        print("\n🔬 SEPARATING BEAT INTO STEMS...")
        print("   Using Demucs AI (Meta AI)")
    
    try:
        # Run Demucs on Replicate (using correct model and version)
        output = replicate.run(
            "ryan5453/demucs:5a7041cc9b82e5a558fea6b3d7b12dea89625e89da33f0447bd727c2d0ab9e77",
            input={
                "audio": open(beat_path, 'rb'),
                "model": "htdemucs_ft",  # Best quality model (fine-tuned hybrid transformer)
                "split": True,  # Enable overlap splitting for best quality
                "overlap": 0.25  # 25% overlap for clean separation
            }
        )
        
        if verbose:
            print("   ✓ Demucs separation complete")
            print("   └─ Downloading stems...")
        
        # Download separated stems
        stems = {}
        stem_names = ['drums', 'bass', 'other']
        
        for stem_name in stem_names:
            if stem_name in output:
                stem_url = output[stem_name]
                stem_path = download_stem(stem_url, stem_name, verbose)
                stems[stem_name] = stem_path
                
                if verbose:
                    print(f"      ✓ {stem_name.capitalize()} stem saved")
        
        if verbose:
            print(f"\n✅ STEM SEPARATION COMPLETE:")
            print(f"   {len(stems)} stems extracted")
            for stem_name in stems:
                print(f"   • {stem_name.capitalize()}")
        
        return stems
    
    except Exception as e:
        raise Exception(f"Stem separation failed: {str(e)}")


def download_stem(url: str, stem_name: str, verbose: bool = False) -> str:
    """
    Download a separated stem from Replicate.
    
    Args:
        url: URL to stem audio
        stem_name: Name of stem (drums/bass/other)
        verbose: Print progress
    
    Returns:
        Path to downloaded stem file
    """
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save stem
        output_path = f"stem_{stem_name}.wav"
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return output_path
    
    except Exception as e:
        raise Exception(f"Failed to download {stem_name} stem: {str(e)}")


def get_stem_loudness(stem_path: str) -> float:
    """
    Get RMS loudness of a stem for mixing balance.
    
    Args:
        stem_path: Path to stem audio
    
    Returns:
        RMS value (0.0 - 1.0)
    """
    try:
        import librosa
        import numpy as np
        
        audio, sr = librosa.load(stem_path, sr=None, mono=True)
        rms = np.sqrt(np.mean(audio**2))
        
        return float(rms)
    
    except Exception:
        return 0.1  # Default fallback
