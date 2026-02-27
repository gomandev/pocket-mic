"""
SUNO API INTEGRATION
====================
Professional beat generation using Suno's AI music API.

This module replaces MusicGen (Replicate) with Suno's superior V5 model
for radio-quality instrumental generation. Uses the "Add Instrumental" API
to generate backing tracks that musically complement uploaded vocals.

Key Features:
- Vocal-aware generation (Suno analyzes uploaded vocal)
- Tag-based style control (genre, mood, BPM, key)
- Model selection (V5 latest, V4_5PLUS for richness)
- Customizable weights (style, audio, creativity)
"""

import requests
import time
import os
from typing import Dict, Optional
from pathlib import Path
import soundfile as sf

# Suno API Configuration
SUNO_API_KEY = "40cf2cf3fd60dac671c9e463b0098ecf"
SUNO_BASE_URL = "https://api.sunoapi.org/api/v1"
POLL_INTERVAL = 5  # seconds between status checks
MAX_POLL_TIME = 300  # 5 minutes timeout


def build_suno_tags(vocal_dna: Dict, blueprint: Dict) -> str:
    """
    Build Suno style tags from vocal DNA and user blueprint.
    
    Tags guide Suno's generation to match the vocal's characteristics
    and user's desired genre/mood.
    
    Args:
        vocal_dna: Extracted vocal characteristics (BPM, key, mood, etc.)
        blueprint: User's style preferences (genre, mood, key)
    
    Returns:
        Comma-separated string of style tags
    """
    genre = blueprint.get("genre", "Alt-R&B")
    mood = blueprint.get("mood", "introspective")
    bpm = vocal_dna.get('bpm', 120)
    key = blueprint.get("key", "D minor")
    
    # Core structural tags
    tags = [
        genre,
        f"{bpm} BPM",
        key
    ]
    
    # Mood-based instrumentation
    mood_instruments = {
        "aggressive": "heavy bass, distorted synths, punchy drums, dark atmosphere",
        "introspective": "ambient pads, soft piano, subtle percussion, atmospheric textures",
        "playful": "bright synths, bouncy bass, melodic elements, upbeat",
        "melancholic": "strings, reverb piano, atmospheric textures, emotional depth",
        "energetic": "driving bass, layered synths, dynamic drums, uplifting",
        "chill": "lo-fi beats, warm pads, smooth bass, relaxed vibe"
    }
    
    tags.append(mood_instruments.get(mood, "atmospheric, melodic, layered"))
    
    # Breath-aware density hints
    breath_count = len(vocal_dna.get('breath_gaps', []))
    if breath_count > 5:
        tags.append("sparse arrangement, space for vocals, breathing instrumentation")
    else:
        tags.append("full arrangement, rich instrumentation, dense production")
    
    # Vocal RMS-based intensity
    rms = vocal_dna.get('rms', 0.1)
    if rms < 0.08:
        tags.append("subtle backing, gentle dynamics")
    elif rms > 0.15:
        tags.append("powerful backing, strong presence")
    
    return ", ".join(tags)


def build_negative_tags(blueprint: Dict) -> str:
    """
    Build tags for elements to exclude from generation.
    
    Args:
        blueprint: User's style preferences
    
    Returns:
        Comma-separated string of negative tags
    """
    # Default exclusions for vocal-forward production
    exclusions = [
        "harsh vocals",
        "screaming",
        "overly aggressive drums",
        "distortion overdrive",
        "muddy mix"
    ]
    
    # Genre-specific exclusions
    genre = blueprint.get("genre", "").lower()
    if "r&b" in genre or "soul" in genre:
        exclusions.extend(["heavy metal", "punk rock", "thrash"])
    
    return ", ".join(exclusions)


def generate_beat_suno(
    vocal_url: str,
    vocal_dna: Dict,
    blueprint: Dict,
    verbose: bool = False
) -> str:
    """
    Generate professional instrumental using Suno's "Add Instrumental" API.
    
    This is the primary beat generation function that replaces MusicGen.
    It uploads the vocal to Suno and generates a musically coherent backing track.
    
    Args:
        vocal_url: Public URL to vocal audio file
        vocal_dna: Extracted vocal characteristics (BPM, key, mood, etc.)
        blueprint: User's style preferences (genre, mood, key)
        verbose: Enable detailed logging
    
    Returns:
        Path to downloaded instrumental audio file
    
    Raises:
        Exception: If generation fails or times out
    """
    
    # Build intelligent tags from vocal analysis
    tags = build_suno_tags(vocal_dna, blueprint)
    negative_tags = build_negative_tags(blueprint)
    
    if verbose:
        print(f"\n🎵 GENERATING SUNO INSTRUMENTAL...")
        print(f"   Genre: {blueprint.get('genre', 'Alt-R&B')}")
        print(f"   Mood: {blueprint.get('mood', 'introspective')}")
        print(f"   Tags: {tags[:100]}...")
        print(f"   Vocal URL: {vocal_url}")
    
    # Step 1: Submit generation task to Suno
    try:
        response = requests.post(
            f"{SUNO_BASE_URL}/generate/add-instrumental",
            headers={
                "Authorization": f"Bearer {SUNO_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "uploadUrl": vocal_url,
                "title": f"{blueprint.get('genre', 'Instrumental')} Production",
                "tags": tags,
                "negativeTags": negative_tags,
                "model": "V5",  # Latest model for best quality
                "styleWeight": 0.65,  # Moderate adherence to style tags
                "audioWeight": 0.75,  # Strong alignment with vocal characteristics
                "weirdnessConstraint": 0.35  # Balanced creativity (not too experimental)
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if verbose:
            print(f"   DEBUG: Suno API response: {result}")
        
        if result.get("code") != 0:
            error_msg = result.get('message', 'Unknown error')
            print(f"   DEBUG: API returned code {result.get('code')}, full response: {result}")
            raise Exception(f"Suno API error: {error_msg}")
        
        task_id = result["data"]["taskId"]
        
        if verbose:
            print(f"   ✓ Task submitted: {task_id}")
            print(f"   └─ Polling for completion...")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to submit Suno task: {str(e)}")
    
    # Step 2: Poll for completion
    beat_url = poll_suno_task(task_id, verbose)
    
    # Step 3: Download generated instrumental
    beat_path = download_suno_audio(beat_url, "generated_beat_suno.wav", verbose)
    
    if verbose:
        print(f"   ✓ Instrumental ready: {beat_path}")
    
    return beat_path


def poll_suno_task(task_id: str, verbose: bool = False) -> str:
    """
    Poll Suno API for task completion and return audio URL.
    
    Args:
        task_id: Task ID from initial generation request
        verbose: Enable logging
    
    Returns:
        URL to generated audio file
    
    Raises:
        Exception: If polling times out or task fails
    """
    start_time = time.time()
    
    while True:
        # Check timeout
        if time.time() - start_time > MAX_POLL_TIME:
            raise Exception(f"Suno generation timeout after {MAX_POLL_TIME}s")
        
        try:
            response = requests.get(
                f"{SUNO_BASE_URL}/generate/get",
                headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
                params={"taskId": task_id},
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"Suno polling error: {result.get('message')}")
            
            data = result.get("data", {})
            status = data.get("status", "pending")
            
            if status == "complete":
                # Get first track URL (Suno returns 2 variations)
                tracks = data.get("data", [])
                if not tracks:
                    raise Exception("No tracks generated")
                
                audio_url = tracks[0].get("audioUrl")
                if not audio_url:
                    raise Exception("No audio URL in response")
                
                if verbose:
                    print(f"   ✓ Generation complete!")
                
                return audio_url
            
            elif status == "failed":
                error = data.get("failReason", "Unknown error")
                raise Exception(f"Suno generation failed: {error}")
            
            else:
                # Still processing
                if verbose:
                    elapsed = int(time.time() - start_time)
                    print(f"   └─ Status: {status} ({elapsed}s elapsed)")
                
                time.sleep(POLL_INTERVAL)
        
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"   ⚠ Poll error: {e}, retrying...")
            time.sleep(POLL_INTERVAL)


def download_suno_audio(url: str, filename: str, verbose: bool = False) -> str:
    """
    Download Suno-generated audio file.
    
    Args:
        url: Audio file URL from Suno
        filename: Local filename to save as
        verbose: Enable logging
    
    Returns:
        Path to downloaded file
    """
    try:
        if verbose:
            print(f"   └─ Downloading audio...")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save to current directory
        filepath = Path(filename)
        filepath.write_bytes(response.content)
        
        return str(filepath)
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download Suno audio: {str(e)}")


# Alternative: Generate instrumental without uploading vocal
def generate_beat_suno_prompt(
    vocal_dna: Dict,
    blueprint: Dict,
    verbose: bool = False
) -> str:
    """
    Generate instrumental from text prompt (without uploading vocal).
    
    This is a fallback method that's faster but less musically coherent
    since Suno doesn't analyze the actual vocal.
    
    Args:
        vocal_dna: Vocal characteristics for prompt building
        blueprint: User's style preferences
        verbose: Enable logging
    
    Returns:
        Path to downloaded instrumental
    """
    tags = build_suno_tags(vocal_dna, blueprint)
    
    if verbose:
        print(f"\n🎵 GENERATING SUNO INSTRUMENTAL (Prompt Mode)...")
        print(f"   Style: {tags[:100]}...")
    
    try:
        response = requests.post(
            f"{SUNO_BASE_URL}/generate/music",
            headers={
                "Authorization": f"Bearer {SUNO_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "V5",
                "customMode": True,
                "instrumental": True,  # Pure instrumental
                "title": f"{blueprint.get('genre', 'Instrumental')} Beat",
                "style": tags
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        task_id = result["data"]["taskId"]
        
        if verbose:
            print(f"   ✓ Task submitted: {task_id}")
        
        # Poll and download
        beat_url = poll_suno_task(task_id, verbose)
        beat_path = download_suno_audio(beat_url, "generated_beat_suno_prompt.wav", verbose)
        
        return beat_path
    
    except Exception as e:
        raise Exception(f"Suno prompt generation failed: {str(e)}")
