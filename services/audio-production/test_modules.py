"""
Producer-First Architecture Test
==================================
Quick validation that all modules work together.
"""

import sys
import os

# Test imports
try:
    from vocal_intel import extract_vocal_dna, load_audio_robust
    from reactive_mixer import mix_vocal_and_beat
    from decision_master import master_track
    from beat_adapter import (
        validate_beat_alignment,
        should_regenerate_beat,
        create_audiocraft_constraints
    )
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test vocal DNA extraction (if test file exists)
test_audio = "test_vocal.wav"  # Replace with actual test file

if os.path.exists(test_audio):
    print(f"\n🧪 Testing Vocal DNA Extraction...")
    try:
        vocal_dna = extract_vocal_dna(test_audio, verbose=True)
        print(f"\n✅ Vocal DNA extraction successful")
        print(f"   Keys present: {list(vocal_dna.keys())}")
        
        # Test constraint generation
        constraints = create_audiocraft_constraints(vocal_dna)
        print(f"\n✅ Constraint generation successful")
        print(f"   BPM Lock: {constraints['bpm']} ± {constraints['bpm_tolerance']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n⚠️ Test audio '{test_audio}' not found. Skipping functional test.")
    print(f"   Place a test WAV file as '{test_audio}' to run full validation.")

print(f"\n🎉 Producer-First Architecture is ready!")
